#!/usr/bin/env python3
"""Check a drafted handoff against its own module's completeness contract.

Every SKILL.md carries the contract in its `## Output profile` block: which
registers are required, the exact columns of each, a minimum row count, and a
blocklist of cell values that disqualify a full run --

    - **critical_cell_values_casefold**: ; [insufficient information];
      insufficient information; n/a; tbd; unknown; not calculable from provided
      materials; not assessable; unavailable

Verifying that by reading means scanning every cell of every register against a
9-value blocklist, per run, while also holding the analysis in mind. That is the
worst possible use of attention: purely mechanical, unbounded in length, and
silently degrading -- a missed placeholder ships as a complete analysis.

The script reads the contract from the module's own SKILL.md, so it cannot
drift from it, and reports violations. It makes no analytical judgment: it
cannot tell whether a figure is RIGHT, only whether the register exists, has the
declared columns, has enough rows, and contains no disqualifying placeholder in
a column declared critical.

    python3 completeness_check.py --skill SKILL.md --handoff DRAFT.md

Exit 0 clean, 1 violations found, 2 could not run.
"""
import argparse
import os
import re
import sys

# Never leave bytecode inside a shipped skill folder. These scripts import a
# sibling (cp_tables), and Python writes __pycache__/*.pyc next to an imported
# module -- so running one from inside the distributed package pollutes the
# package itself, and any integrity check over the tree then reports drift
# against files the build never emitted. Same reason, same line, as the
# packaged CLIs (credit_os_v_cli.py, export_cp_model_v3.py).
sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cp_tables import SEPARATOR_RE, _split_row, parse_tables  # noqa: E402
from validate_handoff import unfenced_markdown  # noqa: E402

BULLET_RE = re.compile(r"^(?P<indent> *)- (?:\*\*(?P<key>[^*]+)\*\*:\s?)?(?P<value>.*)$")
PLACEHOLDERS = {"structured below", ""}
IDENTICAL_TO_COLUMNS = "identical to columns"
PROFILE_PREFIX = "## Output profile"
# A declared column ending in `…N` (U+2026 or three dots, then N), e.g.
# `Period 1…N`, is a template for "one or more columns here", not a literal name.
TEMPLATE_COLUMN_RE = re.compile(r"(?:\u2026|\.\.\.)N$")
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")


# --------------------------------------------------------------------------
# contract side: read the profile out of SKILL.md
# --------------------------------------------------------------------------

PROFILE_MODULE_RE = re.compile(
    r"^## Output profile\s*[—-]\s*binding on\s+(?P<module>CP-[A-Za-z0-9]+)", re.IGNORECASE)


def profile_bodies(skill_text):
    """{module_id_or_None: body} for every `## Output profile` section.

    One entry can carry more than one: cp-5-evidence-trace-validator serves both
    CP-5 and CP-5A and declares a profile for each, with DIFFERENT register sets
    (CP-5 owns T5B.*, CP-5A owns T5.* -- inverted from what the names suggest).

    An earlier version stopped at the first profile, so a CP-5A handoff was
    validated against CP-5's contract and reported all eight of its registers
    missing. Every CP-5A run would have failed its own QA step on a correct
    artifact.
    """
    out, module, body, capturing, in_fence = {}, None, [], False, False
    for line in skill_text.splitlines(keepends=True):
        if FENCE_RE.match(line):
            in_fence = not in_fence
        elif not in_fence and line.startswith("## "):
            if capturing:
                out[module] = "".join(body)
                body = []
            m = PROFILE_MODULE_RE.match(line.rstrip("\n"))
            capturing = line.startswith(PROFILE_PREFIX)
            module = m.group("module").upper() if (capturing and m) else None
            continue
        if capturing:
            body.append(line)
    if capturing:
        out[module] = "".join(body)
    return out


def _profile_body(skill_text, module_id=None):
    """The profile body for `module_id`, or the only one when there is one.

    With several profiles and no module_id, this raises rather than guessing:
    picking the first is exactly the bug this replaced, and silently validating
    against the wrong contract looks like a broken handoff, not a broken check.
    """
    bodies = profile_bodies(skill_text)
    if not bodies:
        return ""
    if module_id:
        key = module_id.strip().upper()
        if key in bodies:
            return bodies[key]
        raise ValueError(
            f"SKILL.md declares no `## Output profile` for {key}; it has "
            f"{sorted(k for k in bodies if k)}")
    if len(bodies) == 1:
        return next(iter(bodies.values()))
    raise ValueError(
        f"SKILL.md declares {len(bodies)} output profiles "
        f"({sorted(k for k in bodies if k)}); pass the handoff's module_id to "
        "select one -- validating against the wrong profile reports every "
        "register of the other module as missing")


def _parse_tree(lines):
    root = {}
    stack = [(-2, root, None)]
    for line in lines:
        m = BULLET_RE.match(line)
        if not m:
            continue
        indent = len(m.group("indent"))
        key = m.group("key")
        value = m.group("value").strip()
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        if key is None:
            parent.setdefault("_items", []).append(value)
            continue
        node = {} if value in PLACEHOLDERS else {"_value": value}
        parent[key.strip()] = node
        stack.append((indent, node, key))
    return root


def _scalar(node):
    if not isinstance(node, dict):
        return node
    if "_value" in node:
        return node["_value"]
    items = node.get("_items")
    if items and len(items) == 1:
        return items[0]
    return None


class ContractError(ValueError):
    """A list in the SKILL.md contract is malformed. `parts` is a best-effort
    plain `;` split, used only so the other items are still checked."""

    def __init__(self, opener, parts):
        super().__init__(f"unbalanced {opener!r}")
        self.parts = parts


def _split_semicolons(raw):
    """Split on `;` only outside (...) and [...], so `Ratchet (direction; bps)`
    stays one column name. `(` and `[` have separate depth counters; a stray
    closer clamps at zero. A list that ends with an opener still open is
    malformed: raise ContractError rather than silently merging items."""
    parts, paren, bracket, cur = [], 0, 0, []
    for ch in raw:
        if ch == "(":
            paren += 1
        elif ch == "[":
            bracket += 1
        elif ch == ")":
            paren = max(0, paren - 1)
        elif ch == "]":
            bracket = max(0, bracket - 1)
        if ch == ";" and paren == 0 and bracket == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    if paren or bracket:
        opener = "(" if paren else "["
        raise ContractError(opener, raw.split(";"))
    return parts


def _list(node, *, keep_empty=False):
    raw = _scalar(node)
    if raw is None and isinstance(node, dict) and "_value" not in node and node.get("_items"):
        raw = ";".join(node.get("_items", []))
    if raw is None or raw.strip().casefold() == "none":
        return []
    return [p.strip() for p in _split_semicolons(raw) if keep_empty or p.strip()]


def _register_list(node, label, errors):
    """`_list` for one register's field. A malformed list is recorded in
    `errors` (check() turns it into a violation naming the register) and the
    plain split stands in so the remaining items are still verified."""
    try:
        return _list(node)
    except ContractError as exc:
        raw = _scalar(node)
        if raw is None:
            raw = ";".join(node.get("_items", []))
        errors.append(f"malformed {label} list ({exc}): \"{raw}\"")
        return [p.strip() for p in exc.parts if p.strip()]


def module_id_of(handoff_text):
    """The handoff's own `module_id`, so the right profile is selected without
    the caller having to know an entry serves two modules."""
    m = re.search(r"^module_id:\s*[\"']?([A-Za-z0-9-]+)", handoff_text, re.MULTILINE)
    return m.group(1).upper() if m else None


def load_contract(skill_text, module_id=None):
    """{'registers': {id: {columns, critical_columns, min_rows, exempt}},
        'blocklist': set, 'substrings': list}"""
    body = _profile_body(skill_text, module_id)
    if not body.strip():
        raise ValueError("SKILL.md has no `## Output profile` section")
    tree = _parse_tree(body.splitlines())
    completeness = tree.get("completeness_contract", {})

    registers = {}
    for reg_id, node in completeness.get("required_registers", {}).items():
        if reg_id.startswith("_") or not isinstance(node, dict):
            continue
        errors = []
        columns = _register_list(node.get("columns", {}), "column", errors)
        crit_raw = _scalar(node.get("critical_columns", {}))
        if crit_raw and crit_raw.strip().casefold() == IDENTICAL_TO_COLUMNS:
            critical = list(columns)
        else:
            critical = _register_list(node.get("critical_columns", {}),
                                      "critical_columns", errors)
        min_rows_raw = _scalar(node.get("minimum_body_rows", {}))
        try:
            min_rows = int(min_rows_raw) if min_rows_raw else 0
        except ValueError:
            min_rows = 0
        registers[reg_id] = {
            "columns": columns,
            "critical_columns": critical,
            "minimum_body_rows": min_rows,
            "disqualifier_exempt_columns": _register_list(
                node.get("disqualifier_exempt_columns", {}),
                "disqualifier_exempt_columns", errors),
            "contract_errors": errors,
        }

    disq = completeness.get("full_run_disqualifiers", {})
    blocklist = {v.casefold() for v in _list(disq.get("critical_cell_values_casefold", {}), keep_empty=True)}
    substrings = [v.casefold() for v in _list(disq.get("critical_cell_substrings_casefold", {}))]

    stable_tables = _list(completeness.get("unconditional_stable_tables_cp_model", {}))

    return {
        "registers": registers,
        "blocklist": blocklist,
        "substrings": substrings,
        "unconditional_stable_tables": stable_tables,
    }


# --------------------------------------------------------------------------
# artifact side: find registers in the drafted handoff
# --------------------------------------------------------------------------

REGISTER_ID_RE = re.compile(r"\b([PT][0-9][A-Za-z0-9.]*|TL[0-9]+\.[0-9]+)\b")


def find_registers(handoff_text, register_ids=None):
    """{register_id: (header, [rows])} for pipe tables labelled with an ID.

    Each row is a list of cells addressed by column index, padded or truncated to
    the header width. Rows are not keyed by header name: headers may repeat
    (`Period 1\u2026N` once per period), and a name-keyed row keeps only the last.

    A register is located by its ID appearing in a heading or caption line
    within the few lines above the table -- which is how these artifacts are
    actually written ("### T4C.4 — Covenant headroom").
    """
    id_re = REGISTER_ID_RE
    if register_ids is not None:
        unique_ids = sorted(set(register_ids), key=lambda value: (-len(value), value))
        if not unique_ids:
            return {}
        alternatives = "|".join(
            re.escape(reg_id)
            for reg_id in unique_ids
        )
        id_re = re.compile(
            rf"(?<![A-Za-z0-9_.])({alternatives})(?![A-Za-z0-9_.])"
        )
    lines = unfenced_markdown(handoff_text).splitlines()
    out, recent = {}, []
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("|") and s.count("|") >= 2 and not SEPARATOR_RE.match(s):
            header = _split_row(s)
            j = i + 1
            if j < len(lines) and SEPARATOR_RE.match(lines[j].strip()) and "|" in lines[j]:
                j += 1
            rows = []
            while j < len(lines):
                t = lines[j].strip()
                if not t.startswith("|"):
                    break
                cells = _split_row(t)
                cells += [""] * (len(header) - len(cells))
                rows.append(cells[:len(header)])
                j += 1
            for label in reversed(recent):
                match = id_re.search(label)
                if match:
                    out.setdefault(match.group(1), (header, rows))
                    break
            i = j
            recent = []
            continue
        if s:
            recent.append(s)
            recent = recent[-4:]
        i += 1
    return out


def is_template_column(name):
    return bool(TEMPLATE_COLUMN_RE.search(name.strip()))


def resolve_columns(declared, header):
    """(problems, period_indexes) for a declared column list against a header.

    Fixed (non-template) columns must all be present. When the contract declares
    a template (it may sit anywhere in the list), the header must be: the fixed
    columns declared before it, in order, as the first cells; one or more period
    cells; then the fixed columns declared after it, in order, as the last cells.
    The period cells are those between, and `period_indexes` are their positions.
    Without a template the check is plain membership, as before.
    """
    fixed = [c for c in declared if not is_template_column(c)]
    first_tmpl = next((i for i, c in enumerate(declared) if is_template_column(c)), None)
    missing = [c for c in fixed if c not in header]
    if missing:
        return [f"missing column(s) {missing}"], []
    if first_tmpl is None:
        return [], []
    pre = [c for c in declared[:first_tmpl] if not is_template_column(c)]
    post = [c for c in declared[first_tmpl:] if not is_template_column(c)]
    if header[:len(pre)] != pre or (post and header[len(header) - len(post):] != post):
        return [f"columns {fixed} are not in the declared order: {pre} must be the "
                f"first column(s) and {post} the last"], []
    if len(header) < len(pre) + len(post) + 1:
        tmpl = [c for c in declared if is_template_column(c)]
        where = (f"after {pre[-1]!r}" if pre else "at the header start")
        if post:
            where += f" and before {post[0]!r}"
        return [f"missing column(s) {tmpl}: at least one column must sit {where}"], []
    return [], list(range(len(pre), len(header) - len(post)))


def check(skill_text, handoff_text, module_id=None):
    contract = load_contract(skill_text, module_id or module_id_of(handoff_text))
    present = find_registers(handoff_text, contract["registers"])
    violations = []

    for reg_id, spec in sorted(contract["registers"].items()):
        violations.extend(f"{reg_id}: {e}" for e in spec["contract_errors"])
        if reg_id not in present:
            violations.append(f"{reg_id}: required register missing from the handoff")
            continue
        header, rows = present[reg_id]
        period_idx = []
        if spec["columns"]:
            problems, period_idx = resolve_columns(spec["columns"], header)
            violations.extend(f"{reg_id}: {p}" for p in problems)
        critical_idx = []
        for col in spec["critical_columns"]:
            if is_template_column(col):
                found = period_idx
            else:
                found = [i for i, name in enumerate(header) if name == col]
                if not found and col not in spec["columns"]:
                    # a declared column is already reported by resolve_columns
                    violations.append(
                        f"{reg_id}: critical column {col!r} matches no header cell")
            critical_idx.extend(i for i in found if i not in critical_idx)
        if len(rows) < spec["minimum_body_rows"]:
            violations.append(
                f"{reg_id}: {len(rows)} body row(s), contract requires "
                f"{spec['minimum_body_rows']}"
            )
        exempt = set(spec["disqualifier_exempt_columns"])
        for n, row in enumerate(rows, 1):
            for idx in critical_idx:
                col = header[idx]
                if col in exempt:
                    continue
                cell = row[idx].casefold().strip()
                if cell in contract["blocklist"]:
                    violations.append(
                        f"{reg_id} row {n}: critical column {col!r} holds a "
                        f"disqualifying placeholder {row[idx]!r}"
                    )
                    continue
                for sub in contract["substrings"]:
                    if sub and sub in cell:
                        violations.append(
                            f"{reg_id} row {n}: critical column {col!r} contains "
                            f"disqualifying text {sub!r}"
                        )
                        break

    try:
        stable_tables = parse_tables(handoff_text)
    except ValueError as exc:
        violations.append(str(exc))
        stable_tables = {}
    for table_id in contract["unconditional_stable_tables"]:
        if table_id not in stable_tables:
            violations.append(
                f"{table_id}: CP-MODEL interface table missing -- it is emitted on "
                "every run, not only when CP-MODEL was requested"
            )

    return violations, contract, present


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill", default="SKILL.md", help="the module's SKILL.md (the contract)")
    ap.add_argument("--handoff", required=True, help="the drafted canonical Markdown handoff")
    ap.add_argument("--module", help="module_id to select an output profile; only needed when the "
                                     "entry serves several and the handoff omits module_id")
    args = ap.parse_args(argv)

    try:
        with open(args.skill, encoding="utf-8") as fh:
            skill_text = fh.read()
        with open(args.handoff, encoding="utf-8") as fh:
            handoff_text = fh.read()
        violations, contract, present = check(skill_text, handoff_text, args.module)
    except (OSError, ValueError) as exc:
        print(f"completeness_check: cannot run -- {exc}", file=sys.stderr)
        return 2

    if not contract["registers"]:
        print("completeness_check: contract declares no registers -- nothing verified",
              file=sys.stderr)
        return 2

    if violations:
        print(f"completeness_check: FAIL ({len(violations)})")
        for v in violations:
            print(f"  - {v}")
        return 1
    print(f"completeness_check: PASS ({len(contract['registers'])} registers, "
          f"{len(present)} found in handoff)")
    return 0


def _self_check():
    skill = """
## Output profile — binding on CP-X's canonical Markdown

- **completeness_contract**: structured below
  - **full_run_disqualifiers**: structured below
    - **critical_cell_substrings_casefold**: source-limited; integration fixture
    - **critical_cell_values_casefold**: ; n/a; tbd; unknown
  - **required_registers**: structured below
    - **T1.1**: structured below
      - **columns**: Item; Value; Evidence ID
      - **critical_columns**: identical to columns
      - **disqualifier_exempt_columns**: none
      - **minimum_body_rows**: 2
  - **unconditional_stable_tables_cp_model**: cpx.model_register

## Companions
"""
    good = """
### T1.1 — Findings
| Item | Value | Evidence ID |
| --- | --- | --- |
| Leverage | 4.2x | E1 |
| Coverage | 2.1x | E2 |

<!-- table-id: cpx.model_register -->
| a |
| --- |
| 1 |
"""
    v, contract, _ = check(skill, good)
    assert v == [], v
    assert contract["registers"]["T1.1"]["critical_columns"] == ["Item", "Value", "Evidence ID"]

    # a blocklisted placeholder in a critical column
    bad = good.replace("| 4.2x |", "| tbd |")
    v, _, _ = check(skill, bad)
    assert any("disqualifying placeholder" in x for x in v), v

    # too few rows
    v, _, _ = check(skill, good.replace("| Coverage | 2.1x | E2 |\n", ""))
    assert any("body row" in x for x in v), v

    # missing column
    v, _, _ = check(skill, good.replace("| Item | Value | Evidence ID |",
                                        "| Item | Value |", 1))
    assert any("missing column" in x for x in v), v

    # missing register entirely
    v, _, _ = check(skill, "no tables here\n")
    assert any("required register missing" in x for x in v), v

    # CP-MODEL interface table absent
    v, _, _ = check(skill, good.replace("<!-- table-id: cpx.model_register -->", ""))
    assert any("CP-MODEL interface table missing" in x for x in v), v

    # substring disqualifier
    v, _, _ = check(skill, good.replace("| 4.2x |", "| source-limited estimate |"))
    assert any("disqualifying text" in x for x in v), v

    # an entry serving two modules: the profile is chosen by the handoff's own
    # module_id, and an ambiguous request raises instead of picking the first
    two = """
## Output profile — binding on CP-5's canonical Markdown

- **completeness_contract**: structured below
  - **required_registers**: structured below
    - **T5B.1**: structured below
      - **columns**: A; B
      - **minimum_body_rows**: 1
  - **full_run_disqualifiers**: structured below
    - **critical_cell_values_casefold**: ; tbd

## Output profile — binding on CP-5A's canonical Markdown

- **completeness_contract**: structured below
  - **required_registers**: structured below
    - **T5.1**: structured below
      - **columns**: A; B
      - **minimum_body_rows**: 1
  - **full_run_disqualifiers**: structured below
    - **critical_cell_values_casefold**: ; tbd

## Companions
"""
    assert sorted(k for k in profile_bodies(two)) == ["CP-5", "CP-5A"], profile_bodies(two)
    assert sorted(load_contract(two, "CP-5")["registers"]) == ["T5B.1"]
    assert sorted(load_contract(two, "CP-5A")["registers"]) == ["T5.1"]
    try:
        load_contract(two)
    except ValueError as exc:
        assert "select one" in str(exc), exc
    else:
        raise AssertionError("ambiguous profile must raise, not pick the first")

    cp5a_handoff = ("---\nmodule_id: CP-5A\n---\n\n### T5.1 — r\n\n| A | B |\n"
                    "| --- | --- |\n| x | y |\n")
    assert module_id_of(cp5a_handoff) == "CP-5A"
    v, c, _ = check(two, cp5a_handoff)
    assert sorted(c["registers"]) == ["T5.1"], c["registers"]
    assert v == [], v

    # `…N` template column: one or more period columns of any name
    tskill = """
## Output profile — binding on CP-X's canonical Markdown

- **completeness_contract**: structured below
  - **full_run_disqualifiers**: structured below
    - **critical_cell_values_casefold**: ; n/a; tbd
  - **required_registers**: structured below
    - **T4.4**: structured below
      - **columns**: Line Item; Period 1\u2026N
      - **critical_columns**: identical to columns
      - **minimum_body_rows**: 1
    - **T4.7**: structured below
      - **columns**: Line Item; Statement Source; Period 1...N
      - **critical_columns**: identical to columns
      - **minimum_body_rows**: 1

## Companions
"""

    def tbl(reg, header, cells):
        n = header.count("|") - 1
        return (f"### {reg} \u2014 r\n{header}\n|{' --- |' * n}\n{cells}\n\n")

    t47 = tbl("T4.7", "| Line Item | Statement Source | FY2024 |", "| a | b | 1 |")
    v, _, _ = check(tskill, tbl("T4.4", "| Line Item | FY2022 | FY2023 |",
                                "| Rev | 1 | 2 |") + t47)
    assert v == [], v
    v, _, _ = check(tskill, tbl("T4.4", "| Line Item |", "| Rev |") + t47)
    assert any("T4.4" in x and "missing column" in x for x in v), v
    v, _, _ = check(tskill, tbl("T4.4", "| Foo | FY2022 |", "| Rev | 1 |") + t47)
    assert any("T4.4" in x and "'Line Item'" in x for x in v), v
    v, _, _ = check(tskill, tbl("T4.4", "| Line Item | FY2022 |", "| Rev | 1 |")
                    + tbl("T4.7", "| Statement Source | Line Item | FY2024 |", "| a | b | 1 |"))
    assert any(x.startswith("T4.7") and "declared order" in x for x in v), v
    v, _, _ = check(tskill, tbl("T4.4", "| Line Item | FY2022 |", "| Rev | tbd |") + t47)
    assert any("FY2022" in x and "placeholder" in x for x in v), v
    v, _, _ = check(tskill, tbl("T4.4", "| Line Item | FY2022 |", "| Rev | 1 |")
                    + tbl("T4.7", "| Line Item | Statement Source |", "| a | b |"))
    assert any(x.startswith("T4.7") and "missing column" in x for x in v), v

    # template in the middle (CP-1b): fixed columns before and after it
    cp1b = tskill.replace("Line Item; Period 1\u2026N\n",
                          "Line Item; Period 1\u2026N; YoY Abs/%; Analyst Note (19 lines)\n", 1)
    mid = "| Line Item | FY2023 | FY2024 | YoY Abs/% | Analyst Note (19 lines) |"
    v, _, _ = check(cp1b, tbl("T4.4", mid, "| Rev | 1 | 2 | 3% | ok |") + t47)
    assert v == [], v
    v, _, _ = check(cp1b, tbl("T4.4", mid, "| Rev | tbd | 2 | 3% | ok |") + t47)
    assert any("FY2023" in x and "placeholder" in x for x in v), v
    v, _, _ = check(cp1b, tbl("T4.4", "| Line Item | YoY Abs/% | Analyst Note (19 lines) |",
                              "| Rev | 3% | ok |") + t47)
    assert any(x.startswith("T4.4") and "missing column" in x for x in v), v
    v, _, _ = check(tskill, tbl("T4.4", "| FY2023 | Line Item | FY2024 |", "| tbd | Rev | 1 |") + t47)
    assert any(x.startswith("T4.4") and "declared order" in x for x in v), v
    # repeated header names: every period cell is checked, not just the last
    v, _, _ = check(tskill, tbl("T4.4", "| Line Item | Period 1\u2026N | Period 1\u2026N |",
                                "| Rev | tbd | 2 |") + t47)
    assert any("row 1" in x and "placeholder" in x for x in v), v

    # `;` inside parentheses/brackets is part of the column name
    pskill = tskill.replace("Line Item; Period 1\u2026N\n",
                            "A; B (x; y); C\n", 1)
    assert load_contract(pskill)["registers"]["T4.4"]["columns"] == ["A", "B (x; y)", "C"]
    v, _, _ = check(pskill, tbl("T4.4", "| A | B (x; y) | C |", "| 1 | 2 | 3 |") + t47)
    assert v == [], v
    v, _, _ = check(pskill, tbl("T4.4", "| A | B (x | y) | C |", "| 1 | 2 | 3 | 4 |") + t47)
    assert any(x.startswith("T4.4") for x in v), v

    # an unbalanced opener is a contract error for that register, never a silent merge
    for opener, text in (("(", "A (x; B; C"), ("[", "A [x; B; C")):
        uskill = tskill.replace("Line Item; Period 1\u2026N\n", text + "\n", 1)
        v, _, _ = check(uskill, tbl("T4.4", "| A | B | C |", "| 1 | 2 | 3 |") + t47)
        want = f"T4.4: malformed column list (unbalanced {opener!r}): \"{text}\""
        assert want in v, v
    # same in critical_columns: reported, and the other critical items still checked
    cskill = tskill.replace(
        "Line Item; Period 1\u2026N\n      - **critical_columns**: identical to columns",
        "B; C\n      - **critical_columns**: A (x; B; C", 1)
    v, _, _ = check(cskill, tbl("T4.4", "| B | C |", "| tbd | 1 |") + t47)
    assert any("T4.4: malformed critical_columns list (unbalanced '(')" in x for x in v), v
    assert any("'B'" in x and "placeholder" in x for x in v), v
    # mixed closer: `]` does not close `(`, so the list is malformed
    mskill = tskill.replace("Line Item; Period 1\u2026N\n", "A; B (x]; C\n", 1)
    v, _, _ = check(mskill, tbl("T4.4", "| A | B | C |", "| 1 | 2 | 3 |") + t47)
    assert any("T4.4: malformed column list (unbalanced '(')" in x for x in v), v
    # mixed but properly nested stays one item
    assert _split_semicolons("A; B (x [y; z]); C") == ["A", " B (x [y; z])", " C"]
    # a critical column that matches no header cell is reported, not skipped
    kskill = tskill.replace(
        "Line Item; Period 1\u2026N\n      - **critical_columns**: identical to columns",
        "A; B\n      - **critical_columns**: A; Bee", 1)
    v, _, _ = check(kskill, tbl("T4.4", "| A | B |", "| 1 | 2 |") + t47)
    assert any(x.startswith("T4.4") and "'Bee'" in x and "no header cell" in x for x in v), v
    v, _, _ = check(kskill.replace("A; Bee", "A; B"), tbl("T4.4", "| A | B |", "| 1 | 2 |") + t47)
    assert v == [], v

    print("completeness_check self-check: OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main())
