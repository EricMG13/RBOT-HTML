"""The methods' shared `completeness_check.py`, run on every module's handoff (harness:
`deploy_workflow.method_scripts`).

The script reads a module's completeness contract from the `## Output profile` of the SKILL.md the
module is sent (the archived bytes, sha256-pinned like the script): each required register's
declared columns, its minimum body rows, the columns it calls critical and the placeholder cells
that disqualify a full run. Its own `load_contract` reads the contract here, so the check cannot
drift from the method; its matching does not run as written, because in this transport:

- registers the scope file cut and the routing registers are not required (`CPOS_REGISTER_SCOPE.md`:
  "not required by the method's ... completeness check"), so only the registers the launcher's
  presence check requires (`cpos_launch.required_registers`) are judged; whether a register is
  present at all stays that check's;
- the CP-MODEL interface tables are not asked for (ROUTING_RULES), so they are not read;
- an explicit gap is the required answer for missing evidence, so a placeholder in a critical
  column, and a register with fewer rows than the method's minimum, are recorded (`noted`), never
  sent back;
- header cells are matched as the harness reads labels (emphasis, case, spacing, `_`, hyphens and a
  trailing unit such as `(USD m)` aside), a joined header (`Currency and scale`) holds each part,
  and a declared column naming a downstream or receiving module is not required (ROUTING_RULES:
  "map upstream or downstream dependencies ... write none of them").

Only a declared column absent from the table under a required register's heading is sent back
(status `missing`), and only for the ten modules with a presence check: no other module's handoff
has been calibrated against it (the retained Sol runs measured the ten). Every other module's
outcomes are recorded as `noted`. A register written only as a gap (`Not supplied: <reason>`),
written as rows instead of columns, or not found as a table under its heading is not checked.
"""

import re
from functools import cache
from typing import Any

from deploy_workflow import method_scripts as core
from deploy_workflow.method_scripts import (
    ROOT,
    SHARED,
    Outcome,
    Status,
    Table,
    _plain,
    _verified,
    blocked,
    register_table,
    registered,
)
from deploy_workflow.owners.cpos_launch_methods import METHODS, REGISTER_SCOPE_MODULES

COMPLETENESS = SHARED + "completeness_check.py"
# A declared column whose rows would address another module (ROUTING_RULES forbids them).
# ROUTING_RULES: "map upstream or downstream dependencies", "keep a ... export record", "a register
# whose rows are addressed to receiving modules": a declared column (or one part of a joined one)
# that is one of these is never required. Checked against every declared column of the ten modules
# (ruling, review of 2026-11-15): `Export Record` (CP-1A T2D.11), `dependency` (CP-2G T2H.8),
# `Responsible Module` (CP-2A T5.5), the `downstream` columns. Kept: `Module Status`, CP-5's
# audited and originating `Module` (provenance), `independence_family`.
ROUTING_COLUMN = re.compile(
    r"downstream|upstream|receiving module|next module|consumer|export record|"
    r"responsible module|^\W*dependenc(?:y|ies)\W*$",
    re.IGNORECASE,
)
MISSING_COLUMNS = (
    "{register} lacks the method's column{s} {names}: its Output profile declares every column of "
    "the register. Write {register}'s table with all of them, under the method's names (a column "
    "with nothing to report holds `Not supplied: <reason>`); a renamed column does not count."
)
SHOWN = 6  # placeholder cells named in one outcome


def _where(module: str, register: str, figure: str, status: Status, reason: str) -> Outcome:
    return Outcome(module, COMPLETENESS, figure, register, figure, status, reason=reason)


def skill(module: str) -> str | None:
    """The archive path of the SKILL.md the module is sent, if it is sent one."""
    sent = [
        p for p in METHODS.get(module, ()) if p.startswith(core.ARCHIVE) and p.endswith("/SKILL.md")
    ]
    return sent[0] if sent else None


@cache
def contract(module: str) -> dict[str, Any] | str:
    """The module's completeness contract as the script's own `load_contract` reads it from the
    sent SKILL.md, or why there is none."""
    path = skill(module)
    if path is None:
        return "the module is sent no SKILL.md"
    loaded = core._loaded(COMPLETENESS)
    text = _verified(ROOT, path, registered()).decode("utf-8")
    try:
        found: dict[str, Any] = loaded.script.load_contract(text, module)
    except ValueError as error:
        return f"its SKILL.md declares no completeness contract: {error}"
    return found


def _norm(text: str) -> str:
    """A header as compared: emphasis, case, `_`, `.`, hyphens and dashes, `?`, footnote marks and
    `<br>` aside, `&` and `+` read as `and`, spacing around `/` and a word's plural `s` ignored
    (`Evidence IDs`)."""
    text = re.sub(r"<br\s*/?>", " ", _plain(text), flags=re.IGNORECASE).casefold().replace("_", " ")
    text = re.sub(r"[†‡§¹²³⁴⁵⁶⁷⁸⁹⁰*]", "", text)
    text = re.sub(r"\s*[&+]\s*", " and ", text)
    text = re.sub(r"[\u2010-\u2015-]", " ", text)
    text = re.sub(r"\?", "", text).replace(".", " ")
    text = re.sub(r"\s*/\s*", "/", text)
    text = re.sub(r"\s+", " ", text).strip(" :")
    return re.sub(r"(?<=\w{2})(?<!s)s\b", "", text)


def _whole(name: str) -> set[str]:
    """A column name as compared: whole, and without what may trail it: a bracketed note (`(USD
    m)`), a scale or range (`1–5`, `(1-5)`), a number mark (`Gap #`, `Gap No.`), a unit after a
    comma (`Revenue, USD m`), a plural mark (`Period(s)`); a bracketed abbreviation is a form
    too (`Free cash flow (FCF)`)."""
    whole = _norm(re.sub(r"\(s\)", "", name))
    short = re.sub(r"\s*\([^()]*\)$", "", whole).strip()
    bare = re.sub(r"(?:\s+(?:\d+(?:\s+\d+)?|#|no))+$", "", short).strip()
    comma = whole.split(",")[0].strip()
    abbreviation = re.findall(r"\((\w+)\)$", whole)
    return {f for f in (whole, short, bare, comma, *abbreviation) if f}


def _parts(name: str) -> set[str]:
    """The parts of a joined name (`a/b`, `a and b`, `a or b`), each as compared."""
    return {p.strip() for w in _whole(name) for p in re.split(r"/| and | or ", w) if p.strip()}


def _spelt(name: str) -> list[set[str]]:
    """Each part of a joined declared name with the words its neighbours share: `gross/net
    leverage` is `gross leverage` and `net leverage`; `opening debt/cash` is `opening debt` and
    `opening cash`; `target/date` may be `target date`. A routing part is left out."""
    whole = _norm(re.sub(r"\(s\)", "", name))
    pieces = [p.strip() for p in re.split(r"/| and | or ", whole) if p.strip()]
    head, tail = pieces[0].split()[0], pieces[-1].split()[-1]
    return [{p, f"{p} {tail}", f"{head} {p}"} for p in pieces if not ROUTING_COLUMN.search(p)]


def _holds(cells: set[str], forms: set[str]) -> bool:
    """A header form is one of ``forms``, or starts or ends with one as whole words (`Principal
    amount`, `Cash interest`)."""
    return bool(forms & cells) or any(
        c.startswith(f + " ") or c.endswith(" " + f) for f in forms for c in cells
    )


def _present(declared: str, header: list[str]) -> bool:
    """A declared column is in the header when a header cell, or a part of a joined one
    (`Currency and scale`), is it or holds it as whole words (`Principal amount`, `Cash
    interest`), or when a joined declared name's parts are each there (`evidence/date` as two
    columns, `gross/net leverage` as `Gross leverage` and `Net leverage`). A part that names a
    routing record (`Export Record`) is not required."""
    cells = set().union(*(_whole(h) | _parts(h) for h in header)) if header else set()
    if _holds(cells, _whole(declared)):
        return True
    spelt = _spelt(declared)
    joined = len(re.split(r"/| and | or ", _norm(declared))) > 1
    return joined and bool(spelt) and all(_holds(cells, forms) for forms in spelt)


# A cell in the transport's gap form: a gap word, or a null word with its reason after a colon.
_GAP_FORM = re.compile(r"^(?:not calculable|not assessable|unavailable|not applicable)\s*:")


def _gap_row(row: list[str]) -> bool:
    """A row that states a gap: a cell in the transport's form (`Not supplied: <reason>`,
    `Not calculable: <reason>`) whatever its other cells say (a label, a source, `n/a`), or a row
    whose cells are mostly the method's placeholder (`[Insufficient Information]`): the presence
    rule's form for a register with nothing to report, under whatever header."""
    said = [_plain(c).casefold() for c in row if _plain(c) not in ("", *core.NOT_APPLICABLE)]
    if any(c.startswith(core.GAP_WORDS[:4]) or _GAP_FORM.match(c) for c in said):
        return True
    gaps = [c for c in said if c.startswith(core.GAP_WORDS) or c in ("n/a", "na", "tbd")]
    return bool(said) and len(gaps) * 2 > len(said)


def tables(text: str, ident: str) -> list[Table] | str:
    """Every table between the register's heading and the next heading of its level or above
    (a register may be written as more than one table, under `####` sub-headings), or why none
    is read."""
    lines = core._unfenced(text)
    starts = [i for i, line in enumerate(lines) if core._register_start(ident).match(line)]
    if len(starts) != 1:
        why = register_table(text, ident)
        return why if isinstance(why, str) else [why]
    start = starts[0]
    level = len(lines[start]) - len(lines[start].lstrip("#")) or 6  # a tag: any heading ends it
    found: list[Table] = []
    for i in range(start + 1, len(lines)):
        heading = core._HEADING.match(lines[i])
        if heading and len(lines[i]) - len(lines[i].lstrip("#")) <= level:
            break
        if lines[i].lstrip().startswith("|") and not lines[i - 1].lstrip().startswith("|"):
            table = core._table_after(lines, i - 1, ident)
            found += [] if isinstance(table, str) else [table]
    return found or f"{ident} has no table under its heading"


def _register(
    module: str, ident: str, spec: dict[str, Any], text: str, enforced: bool
) -> list[Outcome]:
    read = tables(text, ident)
    if isinstance(read, str):
        return [_where(module, ident, "columns", "not checked", read)]
    rows = [row for _, body in read for row in body]
    if rows and all(_gap_row(row) for row in rows):
        why = f"every row of {ident} states a gap, so its columns are not judged"
        return [_where(module, ident, "columns", "not checked", why)]
    out = [_where(module, ident, "contract", "noted", e) for e in spec["contract_errors"]]
    out.append(_columns(module, ident, spec, read, enforced))
    if len(rows) < spec["minimum_body_rows"]:
        why = f"{len(rows)} body row(s); the method's minimum is {spec['minimum_body_rows']}"
        out.append(_where(module, ident, "rows", "noted", why))
    cells = [c for table in read for c in _placeholders(spec, table, contract(module))]
    if cells:
        more = f" and {len(cells) - SHOWN} more" if len(cells) > SHOWN else ""
        why = (
            "not a full analytical run by the method's blocklist (an explicit gap is this "
            f"transport's answer, so recorded only): {'; '.join(cells[:SHOWN])}{more}"
        )
        out.append(_where(module, ident, "placeholders", "noted", why))
    return out


def _columns(
    module: str, ident: str, spec: dict[str, Any], read: list[Table], enforced: bool
) -> Outcome:
    """Whether every declared column (less a routing one) is in one of the register's tables."""
    script = core._loaded(COMPLETENESS).script
    header = [cell for head, _ in read for cell in head]
    fixed = [c for c in spec["columns"] if not script.is_template_column(c)]
    missing = [c for c in fixed if not ROUTING_COLUMN.search(c) and not _present(c, header)]
    if not missing:
        templated = len(fixed) < len(spec["columns"]) and len(read[0][0]) <= len(fixed)
        if templated:
            why = f"{ident} has no period column beside its declared columns"
            return _where(module, ident, "columns", "noted", why)
        return _where(module, ident, "columns", "agreed", "every declared column is present")
    labels = {_norm(row[0]) for _, body in read for row in body if row}
    if any(_whole(m) & labels for m in missing):
        why = f"{ident} is written as rows, not the declared columns; not read"
        return _where(module, ident, "columns", "not checked", why)
    names = ", ".join(f"`{m}`" for m in missing)
    reason = MISSING_COLUMNS.format(register=ident, s="s" * (len(missing) > 1), names=names)
    return _where(module, ident, "columns", "missing" if enforced else "noted", reason)


def _placeholders(spec: dict[str, Any], table: Table, found: Any) -> list[str]:
    """The critical cells of one table holding a placeholder the method's blocklist names."""
    header, rows = table
    exempt = {_norm(c) for c in spec["disqualifier_exempt_columns"]}
    critical = [
        i
        for i, cell in enumerate(header)
        if _norm(cell) not in exempt and any(_present(c, [cell]) for c in spec["critical_columns"])
    ]
    return [
        f"row {n} `{header[i]}`: `{row[i]}`"
        for n, row in enumerate(rows, 1)
        for i in critical
        if _disqualified(row[i], found)
    ]


def _disqualified(cell: str, found: Any) -> bool:
    text = _plain(cell).casefold().strip()
    return text in found["blocklist"] or any(s and s in text for s in found["substrings"])


def check(module: str, text: str) -> list[Outcome]:
    """Each required register's columns, rows and critical cells against the module's contract;
    none for a module sent no SKILL.md."""
    if skill(module) is None:
        return []
    if blocked(text):
        why = "the module stopped at its gate (`module_status: Blocked`): only the gate is owed"
        return [_where(module, "", "all", "not checked", why)]
    found = contract(module)
    if isinstance(found, str):
        return [_where(module, "", "all", "not checked", found)]
    # Imported here: the launcher imports this module.
    from deploy_workflow.owners.cpos_launch import required_registers

    scoped = module in REGISTER_SCOPE_MODULES
    required = set(required_registers(module))
    out: list[Outcome] = []
    for ident, spec in sorted(found["registers"].items()):
        if scoped and ident not in required:
            why = "not required in this transport (register scope or routing rule)"
            out.append(_where(module, ident, "all", "not checked", why))
            continue
        out += _register(module, ident, spec, text, enforced=scoped)
    return out


core.register_shared(COMPLETENESS, check)
