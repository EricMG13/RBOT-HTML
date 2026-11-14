"""Deterministic, fictional loan relative-value market data (SYNTHETIC).

Reproduces the shape of Bloomberg-style loan sheets (columns, dirty cells,
rating buckets); no real issuer, identifier or number is used. Seed and as-of
date come from ``tests/fixtures/market-data/schema.json``.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import random
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

Row = dict[str, str]

DEFAULT_OUT = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "market-data"
MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
NA = "#N/A N/A"
NA_FIELD = "#N/A Field Not Applicable"
NAME_ERR = "#NAME?"
FIGI_CHARS = "0123456789BCDFGHJKLMNPQRSTVWXYZ"

ISSUERS_COLS = (
    "Company",
    "Borrower Name",
    "Core Business Description",
    "Sub-Sector",
    "Sub-Group",
    "Public/Private",
    "Bloomberg ID",
    "FIGI",
    "Loan Type",
    "Ranking",
    "Ratings",
    "Size ($Mn)",
    "Margin",
    "Maturity",
    "Bid",
    "Ask",
    "Δ 1D",
    "Δ 1W",
    "Δ 1M",
    "Δ 3M",
    "Δ 6M",
    "Δ 1YR",
    "Δ YTD",
    "Mid YTM",
    "Mid 3Y DM",
)
PEERS_COLS = (
    "Group",
    "Company",
    "Bloomberg ID",
    "Loan Type",
    "Ranking",
    "Ratings",
    "Size ($Mn)",
    "Margin",
    "Maturity",
    "Bid",
    "Ask",
    "Δ 1M",
    "Δ YTD",
    "Mid YTM",
    "Mid 3Y DM",
)
DELTAS = ("Δ 1D", "Δ 1W", "Δ 1M", "Δ 3M", "Δ 6M", "Δ 1YR", "Δ YTD")
DELTA_MAX_SIXTEENTHS = (2, 4, 8, 16, 24, 32, 32)
AVG_COLS = (
    "Size ($Mn)",
    "Margin",
    "Maturity",
    "Bid",
    "Ask",
    *DELTAS,
    "Mid YTM",
    "Mid 3Y DM",
)
BUCKETS = ("Ba2", "Ba3", "B1", "B2", "B3", "Caa1", "Caa2", "Caa3", "WR")
INDEX_COLS = (
    "Index",
    "Index ID",
    "Market Value ($Bn)",
    "Avg Price",
    *DELTAS,
    "YTM",
    "3Y DM",
)

# (Moody's, S&P, weight, margin range bps)
RATINGS = (
    ("Ba1", "BB+", 1, (150, 175)),
    ("Ba2", "BB", 3, (175, 200)),
    ("Ba3", "BB-", 8, (200, 250)),
    ("B1", "B+", 18, (250, 300)),
    ("B2", "B", 24, (300, 375)),
    ("B3", "B-", 20, (375, 450)),
    ("Caa1", "CCC+", 8, (450, 525)),
    ("Caa2", "CCC", 3, (525, 650)),
    ("WR", "NR", 3, (250, 350)),
)
RANKINGS = (
    ("1L Gtd Sr. Secd", 65),
    ("1L Sr. Secd", 30),
    ("2L Gtd Sr. Secd", 3),
    ("1L SuperP Sr. Secd", 2),
)
LOAN_TYPES = ("B", "B1", "B2", "B3", "B4", "B5", "B6", "C", "FLSO")
PUBLIC_PRIVATE = (("Private", 80), ("Public", 12), ("Public*", 4), ("Private*", 4))
LEGAL = (
    "Holdco LLC",
    "Finco Inc",
    "Intermediate Holdings LLC",
    "Lux Sarl",
    "Holdings Inc",
    "Parent LLC",
    "Group Ltd",
)
SYLLABLES = (
    (
        "Val",
        "Kes",
        "Or",
        "Brin",
        "Tal",
        "Mer",
        "Cor",
        "Ly",
        "Zen",
        "Aur",
        "Fen",
        "Quor",
        "Syl",
        "Dra",
        "Nev",
        "Wex",
    ),
    ("do", "ve", "la", "mi", "ra", "no", "ta", "se"),
    ("ra", "on", "is", "ex", "ia", "um", "ar", "ix"),
)
WORDS = (
    ("Kestrel", "Amber", "Harrow", "Linden", "Marlow", "Northgate", "Opal", "Quarry"),
    ("Ridge", "Point", "Field", "Crest", "Works", "Bay", "Hollow", "Forge"),
)
CUSTOMERS = ("mid-sized enterprises", "regional customers", "institutional clients", "consumers")


@dataclass(frozen=True)
class Spec:
    layout: str
    rows: int
    ratings_average: bool
    groups: tuple[tuple[str, int], ...] = ()


SECTORS: dict[str, Spec] = {
    "entertainment": Spec("issuers", 16, True),
    "telecoms": Spec("issuers", 40, True),
    "it-services": Spec("issuers", 35, True),
    "software": Spec("issuers", 80, True),
    "chemicals": Spec("peers", 24, False, (("Specialty", 12), ("Commodity", 6), ("Adjacent", 6))),
    "healthcare": Spec(
        "peers",
        45,
        False,
        (
            ("Hospitals", 3),
            ("Home Health", 8),
            ("Staffing", 3),
            ("Outsourced Radiology", 3),
            ("Distributors", 1),
            ("Providers/ASC", 14),
            ("Other", 13),
        ),
    ),
    "power": Spec("peers", 27, False, (("Power", 27),)),
}

# sector -> (sub-sector, sub-group, description template)
SUBSECTORS: dict[str, tuple[tuple[str, str, str], ...]] = {
    "entertainment": (
        ("Live Events", "Venues", "Operates ticketed live venues and festivals for {c}."),
        ("Gaming", "Casinos", "Runs regional gaming and hospitality properties for {c}."),
        ("Film & TV", "Production", "Produces and licenses scripted content for {c}."),
        ("Leisure", "Parks", "Operates family leisure and attraction sites for {c}."),
    ),
    "telecoms": (
        ("Wireline", "Fibre", "Builds and leases fibre network capacity to {c}."),
        ("Wireless", "Towers", "Owns shared wireless infrastructure used by {c}."),
        ("Cable", "Broadband", "Provides broadband and video bundles to {c}."),
        ("Satellite", "Services", "Provides satellite connectivity services to {c}."),
    ),
    "it-services": (
        ("Consulting", "Advisory", "Provides technology advisory and delivery services to {c}."),
        ("Managed Services", "Outsourcing", "Runs outsourced IT operations for {c}."),
        ("Data", "Analytics", "Supplies data management and analytics tooling to {c}."),
    ),
    "software": (
        ("Applications", "Vertical", "Sells industry-specific subscription software to {c}."),
        ("Infrastructure", "Security", "Provides cloud security software to {c}."),
        ("Applications", "Horizontal", "Offers workflow and collaboration software to {c}."),
        ("Fintech", "Payments", "Operates payment processing platforms for {c}."),
    ),
}


class Pack:
    """One seeded generator shared by all sectors so identifiers are pack-unique."""

    def __init__(self, seed: int, as_of: date) -> None:
        self.rng = random.Random(seed)
        self.as_of = as_of
        self.used_ids: set[str] = set()
        self.used_names: set[str] = set()

    def pick[T](self, pairs: tuple[tuple[T, int], ...]) -> T:
        return self.rng.choices([p[0] for p in pairs], [p[1] for p in pairs])[0]

    def new_id(self, figi: bool) -> str:
        while True:
            if figi:
                code = "SYN01" + "".join(self.rng.choices(FIGI_CHARS, k=7))
            else:
                code = f"SYN{self.rng.randrange(10**7):07d}"
            if code not in self.used_ids:
                self.used_ids.add(code)
                return code

    def new_company(self) -> str:
        while True:
            if self.rng.random() < 0.4:
                name = f"{self.rng.choice(WORDS[0])} {self.rng.choice(WORDS[1])}"
            else:
                name = "".join(self.rng.choice(s) for s in SYLLABLES)
            if name not in self.used_names:
                self.used_names.add(name)
                return name

    def rating(self) -> tuple[str, str, tuple[int, int]]:
        idx = self.rng.choices(range(len(RATINGS)), [r[2] for r in RATINGS])[0]
        moodys, sp, _, margin = RATINGS[idx]
        if moodys != "WR" and self.rng.random() < 0.03:  # off-diagonal pair
            sp = RATINGS[min(7, idx + 1)][1]
        return moodys, sp, margin

    def maturity(self) -> date:
        lo, hi = date(2027, 11, 1).toordinal(), date(2033, 6, 30).toordinal()
        return date.fromordinal(self.rng.randint(lo, hi))

    def margin(self, bounds: tuple[int, int]) -> Decimal:
        value = Decimal(25 * self.rng.randint(bounds[0] // 25, bounds[1] // 25))
        if self.rng.random() >= 0.03:
            return value
        half = value - Decimal("7.5")
        return half if half >= bounds[0] else value + Decimal("7.5")

    def prices(self, moodys: str) -> tuple[Decimal, Decimal]:
        rng = self.rng
        if moodys.startswith("Caa"):
            low = 50 if rng.random() < 0.06 else 68
            bid_n = rng.randint(low * 8, 95 * 8)
            ask_n = bid_n + rng.randint(4, 20)
        else:
            lo, hi = (95, 100) if moodys == "B3" else (98.5, 100.5)
            bid_n = rng.randint(int(lo * 8), int(hi * 8))
            ask_n = bid_n + rng.randint(2, 6)
        return Decimal(bid_n) / 8, Decimal(ask_n) / 8

    def deltas(self, moodys: str) -> Row:
        scale = 4 if moodys.startswith("Caa") else 2 if moodys == "B3" else 1
        out: Row = {}
        for name, top in zip(DELTAS, DELTA_MAX_SIXTEENTHS, strict=True):
            zero = name == "Δ 1D" and self.rng.random() < 0.4
            out[name] = trim(
                Decimal(0 if zero else self.rng.randint(-top * scale, top * scale)) / 16
            )
        return out

    def loan(self, moodys: str, bounds: tuple[int, int]) -> Row:
        mat = self.maturity()
        margin = self.margin(bounds)
        bid, ask = self.prices(moodys)
        mid = (bid + ask) / 2
        years = max(0.5, round((mat - self.as_of).days / 365.25, 1))
        gap = float(100 - mid)
        ytm = 3.9 + float(margin) / 100 + gap / years + self.rng.uniform(-0.1, 0.1)
        dm = float(margin) + gap * 41.5 + self.rng.uniform(-8, 8)
        return {
            "Ranking": self.pick(RANKINGS),
            "Size ($Mn)": str(5 * self.rng.randint(60, 1200))
            if self.rng.random() < 0.9
            else str(self.rng.randint(300, 6000)),
            "Margin": trim(margin),
            "Maturity": f"{mat.day:02d}-{MONTHS[mat.month - 1]}-{mat.year % 100:02d}",
            "Bid": trim(bid),
            "Ask": trim(ask),
            **self.deltas(moodys),
            "Mid YTM": f"{ytm:.1f}",
            "Mid 3Y DM": str(round(dm)),
        }

    def dirty(self, row: Row) -> None:
        for name in DELTAS:
            if self.rng.random() < 0.06:
                row[name] = NA
        if self.rng.random() < 0.03:
            row["Ratings"] = f"{NA} / {row['Ratings'].rsplit(' / ', 1)[1]}"
        if self.rng.random() < 0.08:
            row["Loan Type"] = NA_FIELD

    def issuer_rows(self, spec: Spec, sector: str) -> list[Row]:
        rows: list[Row] = []
        while len(rows) < spec.rows:
            company = self.new_company()
            sub, group, template = self.rng.choice(SUBSECTORS[sector])
            moodys, sp, bounds = self.rating()
            count = self.rng.choice((2, 3)) if self.rng.random() < 0.12 else 1
            types = ["B"] if self.rng.random() < 0.75 else [self.rng.choice(LOAN_TYPES)]
            while len(types) < count:
                types.append(self.rng.choice([t for t in LOAN_TYPES if t not in types]))
            borrower = f"{company} {self.rng.choice(LEGAL)}"
            desc = template.format(c=self.rng.choice(CUSTOMERS))
            visibility = self.pick(PUBLIC_PRIVATE)
            for loan_type in types[: spec.rows - len(rows)]:
                row: Row = {
                    "Company": company,
                    "Borrower Name": borrower,
                    "Core Business Description": desc,
                    "Sub-Sector": sub,
                    "Sub-Group": group,
                    "Public/Private": visibility,
                    "Bloomberg ID": self.new_id(False),
                    "FIGI": self.new_id(True),
                    "Loan Type": loan_type,
                    "Ratings": f"{moodys} / {sp}",
                    **self.loan(moodys, bounds),
                }
                self.dirty(row)
                rows.append(row)
        return sorted(rows, key=lambda r: r["Company"])

    def peer_rows(self, spec: Spec) -> list[Row]:
        rows: list[Row] = []
        for group, count in spec.groups:
            for _ in range(count):
                moodys, sp, bounds = self.rating()
                row: Row = {
                    "Group": group,
                    "Company": self.new_company(),
                    "Bloomberg ID": self.new_id(self.rng.random() < 0.4),
                    "Loan Type": "B" if self.rng.random() < 0.75 else self.rng.choice(LOAN_TYPES),
                    "Ratings": f"{moodys} / {sp}",
                    **self.loan(moodys, bounds),
                }
                self.dirty(row)
                rows.append(row)
        return rows

    def build(self, name: str) -> list[Row]:
        spec = SECTORS[name]
        rows = self.issuer_rows(spec, name) if spec.layout == "issuers" else self.peer_rows(spec)
        if name == "healthcare":
            broken = self.rng.choice(rows)
            for col in PEERS_COLS:
                if col not in ("Bloomberg ID", "Group"):  # Group kept: schema counts rows per group
                    broken[col] = NAME_ERR
        if name == "power":
            unpriced = self.rng.choice(rows)
            for col in ("Bid", "Ask", "Δ 1M", "Δ YTD", "Mid YTM", "Mid 3Y DM"):
                unpriced[col] = NA
        return rows


def trim(value: Decimal) -> str:
    return format(value.normalize(), "f")


def fmt_date(day: date) -> str:
    return f"{day.day:02d}-{MONTHS[day.month - 1]}-{day.year % 100:02d}"


def parse_date(text: str) -> date | None:
    parts = text.split("-")
    if len(parts) != 3 or parts[1] not in MONTHS:
        return None
    return date(2000 + int(parts[2]), MONTHS.index(parts[1]) + 1, int(parts[0]))


def parse_num(text: str) -> Decimal | None:
    try:
        return Decimal(text) if text[:1] in "-0123456789" else None
    except ArithmeticError:
        return None


def mean(values: list[Decimal]) -> str:
    return (
        trim(
            (sum(values, Decimal(0)) / len(values)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        )
        if values
        else "-"
    )


def average_column(col: str, rows: list[Row]) -> str:
    if col == "Maturity":
        days = [d.toordinal() for r in rows if (d := parse_date(r[col]))]
        return fmt_date(date.fromordinal(round(sum(days) / len(days)))) if days else "-"
    return mean([n for r in rows if (n := parse_num(r[col])) is not None])


def ratings_average(rows: list[Row]) -> list[list[str]]:
    out = []
    for bucket in BUCKETS:
        members = [r for r in rows if r["Ratings"].rsplit(" / ", 1)[0] == bucket]
        cells = [average_column(c, members) for c in AVG_COLS] if members else ["-"] * len(AVG_COLS)
        out.append([bucket, str(len(members)), *cells])
    return out


def index_rows(pack: Pack) -> list[list[str]]:
    anchors = (
        ("Ba", 340, "99.2", "6.0", 238),
        ("Ba/B", 1250, "97.0", "7.5", 401),
        ("B", 900, "96.0", "8.0", 463),
        ("Caa", 85, "76.5", "18.4", 1522),
    )
    rng = pack.rng
    out = []
    for i, (name, value, price, ytm, dm) in enumerate(anchors, start=1):
        wide = 3 if name == "Caa" else 1
        deltas = [
            trim(Decimal(rng.randint(-top * wide, top * wide)) / 16)
            for top in (1, 2, 4, 8, 12, 16, 16)
        ]
        out.append(
            [
                f"Synthetic Leveraged Loan Index: {name}",
                f"SYNIDX{i:02d}",
                f"{value * rng.uniform(0.9, 1.1):.1f}",
                f"{float(price) + rng.uniform(-0.1, 0.1):.2f}",
                *deltas,
                f"{float(ytm) + rng.uniform(-0.15, 0.15):.1f}",
                str(dm + rng.randint(-8, 8)),
            ]
        )
    return out


def write_csv(path: Path, header: tuple[str, ...], rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


ISSUER_SECTOR = "telecoms"
QUOTE_COLS = (
    "Bloomberg ID",
    "Loan Type",
    "Ranking",
    "Ratings",
    "Size ($Mn)",
    "Margin",
    "Maturity",
    "Bid",
    "Ask",
    "Mid YTM",
    "Mid 3Y DM",
)
QUOTE_PROVIDER = "Synthetic loan pack"


def clean_tranche(row: Row) -> bool:
    cells = (row["Loan Type"], *row["Ratings"].split(" / "), *(row[c] for c in QUOTE_COLS[7:]))
    return not any(cell.startswith("#") for cell in cells)


def issuer_tranches(rows: list[Row]) -> list[Row]:
    """The first company, in file order, with two or more tranches that are all clean."""
    for company in dict.fromkeys(r["Company"] for r in rows):
        tranches = [r for r in rows if r["Company"] == company]
        if len(tranches) >= 2 and all(clean_tranche(r) for r in tranches):
            return tranches
    raise ValueError(f"no {ISSUER_SECTOR} company has two or more clean tranches")


def write_issuer_files(out_dir: Path, rows: list[Row], as_of: date) -> None:
    """One fictional issuer in the shape of an issuer's market files.

    Synthetic, not issuer evidence. Writes a quotes file and the matching context quote rows.
    """
    tranches = issuer_tranches(rows)
    head = tranches[0]
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(QUOTE_COLS)
    writer.writerows([r[c] for c in QUOTE_COLS] for r in tranches)
    text = "SYNTHETIC FIXTURE - not issuer evidence.\n"
    text += f"Loan quotes as of {as_of.isoformat()} - {head['Company']} ({head['Borrower Name']})\n"
    (out_dir / "issuer-quotes.txt").write_text(
        text + buffer.getvalue(), encoding="utf-8", newline="\n"
    )
    quotes = [
        {
            "facility_id": r["Bloomberg ID"],
            "kind": "observed",
            "bid": r["Bid"],
            "ask": r["Ask"],
            "price": trim((Decimal(r["Bid"]) + Decimal(r["Ask"])) / 2),
            "yield_pct": r["Mid YTM"],
            "spread_bps": r["Mid 3Y DM"],
            "as_of": as_of.isoformat(),
            "provider": QUOTE_PROVIDER,
        }
        for r in tranches
    ]
    text = json.dumps(quotes, indent=2, ensure_ascii=False) + "\n"
    (out_dir / "issuer-context-quotes.json").write_text(text, encoding="utf-8", newline="\n")


README = """# Synthetic loan market data (SYNTHETIC)
All names, ids and numbers are invented; only the shape of Bloomberg-style loan sheets stays.
Regenerate: `uv run python tools/synthetic_market_data.py` (seed and as-of from schema.json).
`schema.json` is the answer key for tests/test_synthetic_market_data.py. Files: `<sector>.csv`,
`<sector>-ratings-average.csv` (issuer-layout sectors) and `index-statistics.csv`.
Dirty cells are literal: `#N/A N/A` (price changes, Moody's rating), `#N/A Field Not Applicable`.
A Delta of `0` is a real zero; a dirty token is missing data, never zero.
Healthcare: one row holds `#NAME?` in every column except Bloomberg ID and Group.
Power: one unpriced row has `#N/A N/A` in Bid, Ask, Delta 1M, Delta YTD, Mid YTM, Mid 3Y DM.
Peers Bloomberg ID mixes `SYN`+7 digits and FIGI-style `SYN01`+7 chars. No colours.
`issuer-quotes.txt` is read by the run-start classifier as `market_quotes` (clears CP-3 and CP-3D
no-quotes gaps); `issuer-context-quotes.json` holds the same tranches as run-context `quotes` rows.
Both are one telecoms issuer (first with two clean tranches); sector peer sheets stay unrecognised.
"""


def main(out_dir: Path = DEFAULT_OUT) -> None:
    schema = json.loads((DEFAULT_OUT / "schema.json").read_text(encoding="utf-8"))
    pack = Pack(schema["seed"], date.fromisoformat(schema["as_of"]))
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, spec in SECTORS.items():
        cols = ISSUERS_COLS if spec.layout == "issuers" else PEERS_COLS
        rows = pack.build(name)
        if name == ISSUER_SECTOR:
            write_issuer_files(out_dir, rows, pack.as_of)
        write_csv(out_dir / f"{name}.csv", cols, [[r[c] for c in cols] for r in rows])
        if spec.ratings_average:
            header = ("Rating", "# Issuers", *AVG_COLS)
            write_csv(out_dir / f"{name}-ratings-average.csv", header, ratings_average(rows))
    write_csv(out_dir / "index-statistics.csv", INDEX_COLS, index_rows(pack))
    (out_dir / "README.md").write_text(README, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("out_dir", nargs="?", type=Path, default=DEFAULT_OUT)
    main(parser.parse_args().out_dir)
