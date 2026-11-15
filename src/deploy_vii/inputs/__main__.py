"""The input self-check command (`KINDS`), run before a file is uploaded or prepared.

    uv run deploy-vii validate-input portfolio <file> [--as-of YYYY-MM-DD] [--json]
    uv run deploy-vii validate-input portfolio-exports <folder or files> [--as-of YYYY-MM-DD]
    uv run deploy-vii validate-input rv <file> [--json]

`portfolio-exports` (also `portfolio-export`) takes the fund's export together, as files or as a
folder that holds them: the mandate, constraints and exposure report as CSV files or workbook
sheets, and the holdings workbook, in any order (`deploy_vii.inputs.portfolio_export`). It prints
a reconciliation table of the headline figures, stated against the holdings, before the findings.

It prints one line per issue and then a summary (`--json`: the report as JSON) and exits 0 when the
file passes, 1 when it does not and 2 on a usage error. `--as-of` is the run's as-of date: the
portfolio workbook's or export's dates are then checked against it, as the launcher checks them.
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from deploy_vii.inputs import KINDS
from deploy_vii.inputs.portfolio import validate_portfolio
from deploy_vii.inputs.portfolio_export import ExportReport, validate_export_paths
from deploy_vii.inputs.rv_quotes import ValidationReport

EXPORTS = ("portfolio-exports", "portfolio-export")
DATED = ("portfolio", *EXPORTS)
_READ = (".csv", ".xlsx")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deploy-vii", description="Check an input file.")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate-input", help="check one input file before using it")
    check.add_argument("kind", choices=sorted({*KINDS, *EXPORTS}))
    check.add_argument("file", type=Path, nargs="+")
    check.add_argument(
        "--as-of",
        type=date.fromisoformat,
        help="the run's as-of date, YYYY-MM-DD (portfolio and portfolio-exports): also check the "
        "dates against it",
    )
    check.add_argument("--json", action="store_true", help="print the report as JSON")
    return parser


def _files(paths: Sequence[Path]) -> list[Path]:
    """The given files, with each folder replaced by the CSV and XLSX files in it (hidden files
    and Office lock files left out)."""
    out: list[Path] = []
    for path in paths:
        if not path.is_dir():
            out.append(path)
            continue
        out += sorted(
            found
            for found in path.rglob("*")
            if found.is_file()
            and found.suffix.lower() in _READ
            and not any(part.startswith((".", "~$")) for part in found.relative_to(path).parts)
        )
    return out


def _check(kind: str, files: Sequence[Path], as_of: date | None) -> ValidationReport:
    if kind in EXPORTS:
        return validate_export_paths(_files(files), run_date=as_of)
    if kind == "portfolio":
        return validate_portfolio(files[0], run_date=as_of)
    return KINDS[kind](files[0])


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.as_of is not None and args.kind not in DATED:
        parser.error("--as-of applies to the portfolio workbook and the portfolio export only")
    if args.kind not in EXPORTS and len(args.file) != 1:
        parser.error(f"{args.kind} takes one file")
    result = _check(args.kind, args.file, args.as_of)
    if args.json:
        sys.stdout.write(result.model_dump_json(indent=2) + "\n")
    else:
        table = result.table_lines() if isinstance(result, ExportReport) else ()
        sys.stdout.write("\n".join((*table, *(("",) if table else ()), *result.lines())) + "\n")
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
