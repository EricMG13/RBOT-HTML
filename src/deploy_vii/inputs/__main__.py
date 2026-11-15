"""The input self-check command (`KINDS`), run before a file is uploaded or prepared.

    uv run deploy-vii validate-input portfolio <file> [--as-of YYYY-MM-DD] [--json]
    uv run deploy-vii validate-input portfolio-export <files> [--as-of YYYY-MM-DD] [--json]
    uv run deploy-vii validate-input rv <file> [--json]

`portfolio-export` takes the export's files together (mandate, constraints and exposure report
CSVs and the holdings workbook, in any order; `deploy_vii.inputs.portfolio_export`).

It prints one line per issue and then a summary (`--json`: the report as JSON) and exits 0 when the
file passes, 1 when it does not and 2 on a usage error. `--as-of` is the run's as-of date: the
portfolio workbook's dates are then checked against it, as the launcher checks them.
"""

import argparse
import sys
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from deploy_vii.inputs import KINDS
from deploy_vii.inputs.portfolio import validate_portfolio
from deploy_vii.inputs.portfolio_export import validate_export_paths
from deploy_vii.inputs.rv_quotes import ValidationReport

EXPORT = "portfolio-export"
DATED = ("portfolio", EXPORT)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deploy-vii", description="Check an input file.")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate-input", help="check one input file before using it")
    check.add_argument("kind", choices=sorted({*KINDS, EXPORT}))
    check.add_argument("file", type=Path, nargs="+")
    check.add_argument(
        "--as-of",
        type=date.fromisoformat,
        help="the run's as-of date, YYYY-MM-DD (portfolio and portfolio-export): also check the "
        "dates against it",
    )
    check.add_argument("--json", action="store_true", help="print the report as JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.as_of is not None and args.kind not in DATED:
        parser.error("--as-of applies to the portfolio workbook and the portfolio export only")
    if args.kind != EXPORT and len(args.file) != 1:
        parser.error(f"{args.kind} takes one file")
    result: ValidationReport
    if args.kind == EXPORT:
        result = validate_export_paths(args.file, run_date=args.as_of)
    elif args.kind == "portfolio":
        result = validate_portfolio(args.file[0], run_date=args.as_of)
    else:
        result = KINDS[args.kind](args.file[0])
    sys.stdout.write(
        result.model_dump_json(indent=2) + "\n" if args.json else "\n".join(result.lines()) + "\n"
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    sys.exit(main())
