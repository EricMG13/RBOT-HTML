"""Synthetic market-data pack: determinism and conformance to schema.json (the answer key)."""

import csv
import json
from collections import Counter
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

import pytest

from deploy_workflow.context import load_context
from deploy_workflow.run_expectations import RULES, Facts, guess_kind
from tools import synthetic_market_data

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "market-data"
SCHEMA = json.loads((FIXTURES / "schema.json").read_text(encoding="utf-8"))
SECTORS = SCHEMA["sectors"]
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def load(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    return rows[0], [dict(zip(rows[0], r, strict=True)) for r in rows[1:]]


def to_date(text: str) -> date:
    day, mon, yy = text.split("-")
    return date(2000 + int(yy), MONTHS.index(mon) + 1, int(day))


@pytest.fixture(scope="module")
def regenerated(tmp_path_factory: pytest.TempPathFactory) -> Path:
    out = tmp_path_factory.mktemp("pack")
    synthetic_market_data.main(out)
    return out


def test_regeneration_is_byte_identical(regenerated: Path) -> None:
    generated = {p.name for p in regenerated.iterdir() if not p.name.startswith(".")}
    committed_data = {
        p.name
        for p in FIXTURES.iterdir()
        if not p.name.startswith(".")
        and p.suffix in {".csv", ".txt", ".json"}
        and p.name != "schema.json"
    }
    assert committed_data <= generated, "committed data file the generator does not write"
    for name in generated:
        assert (regenerated / name).read_bytes() == (FIXTURES / name).read_bytes(), name


@pytest.mark.parametrize("sector", sorted(SECTORS))
def test_sector_matches_schema(sector: str) -> None:
    spec = SECTORS[sector]
    header, rows = load(FIXTURES / f"{sector}.csv")
    assert header == SCHEMA["layouts"][spec["layout"]]
    assert len(rows) == spec["rows"]
    if "groups" in spec:
        assert dict(Counter(r["Group"] for r in rows)) == spec["groups"]
        assert list(dict.fromkeys(r["Group"] for r in rows)) == list(spec["groups"])
    for row in (r for r in rows if r["Loan Type"] != "#NAME?"):  # that row is dirty by design
        assert not row["Bloomberg ID"].startswith(tuple(SCHEMA["forbidden_id_prefixes"]))
        assert to_date(row["Maturity"]) > date.fromisoformat(SCHEMA["as_of"])
        if not row["Bid"].startswith("#"):
            assert float(row["Bid"]) <= float(row["Ask"])


def test_ids_unique_across_pack() -> None:
    ids = []
    for sector in SECTORS:
        _, rows = load(FIXTURES / f"{sector}.csv")
        ids += [r["Bloomberg ID"] for r in rows] + [r["FIGI"] for r in rows if "FIGI" in r]
    assert len(ids) == len(set(ids))


def test_dirty_tokens_and_special_rows() -> None:
    cells = [c for s in SECTORS for r in load(FIXTURES / f"{s}.csv")[1] for c in r.values()]
    for token in SCHEMA["dirty_tokens"]:
        assert token in cells
    _, entertainment = load(FIXTURES / "entertainment.csv")
    _, software = load(FIXTURES / "software.csv")
    assert any(r["Δ 1D"] == "0" for r in entertainment + software)  # a true zero is not N/A
    _, health = load(FIXTURES / "healthcare.csv")
    broken = [r for r in health if r["Loan Type"] == "#NAME?"]
    assert len(broken) == 1
    assert all(v == "#NAME?" for k, v in broken[0].items() if k not in ("Bloomberg ID", "Group"))
    _, power = load(FIXTURES / "power.csv")
    unpriced = [r for r in power if r["Bid"] == "#N/A N/A"]
    assert len(unpriced) == 1
    assert all(
        unpriced[0][c] == "#N/A N/A" for c in ("Ask", "Δ 1M", "Δ YTD", "Mid YTM", "Mid 3Y DM")
    )
    assert float(unpriced[0]["Margin"]) > 0 and to_date(unpriced[0]["Maturity"])


@pytest.mark.parametrize("sector", [s for s, v in SECTORS.items() if v["ratings_average"]])
def test_ratings_average_counts(sector: str) -> None:
    _, rows = load(FIXTURES / f"{sector}.csv")
    header, avg = load(FIXTURES / f"{sector}-ratings-average.csv")
    assert header == SCHEMA["ratings_average_columns"]
    assert [r["Rating"] for r in avg] == SCHEMA["ratings_average_buckets"]
    for bucket in avg:
        expected = sum(1 for r in rows if r["Ratings"].split(" / ")[0] == bucket["Rating"])
        assert bucket["# Issuers"] == str(expected)
        if expected == 0:
            assert all(v == "-" for k, v in bucket.items() if k not in ("Rating", "# Issuers"))


def test_index_statistics() -> None:
    header, rows = load(FIXTURES / "index-statistics.csv")
    assert header == SCHEMA["index_columns"]
    assert len(rows) == SCHEMA["index_rows"]
    bounds = {k: v for k, v in SCHEMA["index_bounds"].items() if not k.startswith("_")}
    delta_cols = [c for c in header if c.startswith("\u0394")]
    assert sorted(r["Index"].rsplit(": ", 1)[1] for r in rows) == sorted(bounds)
    for row in rows:
        suffix = row["Index"].rsplit(": ", 1)[1]
        spec = dict(bounds[suffix])
        delta_max = Decimal(str(spec.pop("delta_abs_max")))
        for col, (low, high) in spec.items():
            assert Decimal(str(low)) <= Decimal(row[col]) <= Decimal(str(high)), (suffix, col)
        for col in delta_cols:
            assert abs(Decimal(row[col])) <= delta_max, (suffix, col)


def numeric(cell: str) -> Decimal | None:
    return Decimal(cell) if cell[:1] in "-0123456789" else None


def written_mean(values: list[Decimal]) -> str:
    """Arithmetic mean, 2 dp half-up, trailing zeros trimmed; '-' when nothing is numeric."""
    if not values:
        return "-"
    cents = (sum(values, Decimal(0)) / len(values)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return f"{cents:.2f}".rstrip("0").rstrip(".")


def written_mean_date(texts: list[str]) -> str:
    """Mean of the day numbers rounded to the nearest day (an exact half goes to the even day)."""
    days = [to_date(t).toordinal() for t in texts if t[:1].isdigit()]
    if not days:
        return "-"
    mean_day = date.fromordinal(round(Fraction(sum(days), len(days))))
    return f"{mean_day.day:02d}-{MONTHS[mean_day.month - 1]}-{mean_day.year % 100:02d}"


@pytest.mark.parametrize("sector", [s for s, v in SECTORS.items() if v["ratings_average"]])
def test_ratings_average_every_column_recomputed(sector: str) -> None:
    _, rows = load(FIXTURES / f"{sector}.csv")
    header, avg = load(FIXTURES / f"{sector}-ratings-average.csv")
    averaged = [c for c in header if c not in ("Rating", "# Issuers")]
    assert len(averaged) == 14
    for bucket in avg:
        members = [r for r in rows if r["Ratings"].split(" / ")[0] == bucket["Rating"]]
        for col in averaged:
            if col == "Maturity":
                expected = written_mean_date([r[col] for r in members])
            else:
                nums = [n for r in members if (n := numeric(r[col])) is not None]
                expected = written_mean(nums)
            assert bucket[col] == expected, (sector, bucket["Rating"], col)


def test_ratings_average_cells_round_half_up() -> None:
    cols = ("Size ($Mn)", "Margin", "Bid", "Ask")
    for sector in (s for s, v in SECTORS.items() if v["ratings_average"]):
        _, rows = load(FIXTURES / f"{sector}.csv")
        _, avg = load(FIXTURES / f"{sector}-ratings-average.csv")
        for bucket in avg:
            members = [r for r in rows if r["Ratings"].split(" / ")[0] == bucket["Rating"]]
            for col in cols:
                nums = [Decimal(r[col]) for r in members if not r[col].startswith("#")]
                if not nums:
                    continue
                mean = sum(nums, Decimal(0)) / len(nums)
                expected = mean.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                assert Decimal(bucket[col]) == expected, (sector, bucket["Rating"], col)


BANDS = {
    "Ba1": (150, 175),
    "Ba2": (175, 200),
    "Ba3": (200, 250),
    "B1": (250, 300),
    "B2": (300, 375),
    "B3": (375, 450),
    "Caa1": (450, 525),
    "Caa2": (525, 650),
    "WR": (250, 350),
}


@pytest.mark.parametrize("sector", sorted(SECTORS))
def test_margin_inside_rating_band(sector: str) -> None:
    _, rows = load(FIXTURES / f"{sector}.csv")
    for row in rows:
        moodys = row["Ratings"].split(" / ")[0]
        if moodys in BANDS and not row["Margin"].startswith("#"):
            lo, hi = BANDS[moodys]
            assert lo <= Decimal(row["Margin"]) <= hi, (row["Bloomberg ID"], moodys)


ISSUER = SCHEMA["issuer"]


def quotes_text() -> str:
    return "\n".join(ISSUER["quotes_text"]) + "\n"


def test_issuer_files_equal_the_key(regenerated: Path) -> None:
    assert (regenerated / ISSUER["quotes_file"]).read_text(encoding="utf-8") == quotes_text()
    written = json.loads((regenerated / ISSUER["context_quotes_file"]).read_text(encoding="utf-8"))
    assert written == ISSUER["context_quotes"]


def quotes_context() -> bytes:
    data = json.loads((ROOT / "cases" / "context" / "research-minimal.json").read_text("utf-8"))
    data["quotes"] = ISSUER["context_quotes"]
    return json.dumps(data).encode()


def test_quotes_file_is_read_as_market_quotes_and_context_loads() -> None:
    guess = guess_kind(ISSUER["quotes_file"], [quotes_text()])
    assert guess.kind == ISSUER["document_kind"]
    quotes = load_context(quotes_context()).quotes
    assert [q.kind for q in quotes] == ["observed", "observed"]


def test_issuer_quotes_clear_the_no_quotes_rules() -> None:
    bare = load_context((ROOT / "cases" / "context" / "research-minimal.json").read_bytes())
    with_quotes = load_context(quotes_context())
    guesses = (guess_kind(ISSUER["quotes_file"], [quotes_text()]),)
    ordered = ("CP-3", "CP-3D")
    by_key = {r.key: r for r in RULES}
    for key in ISSUER["rules_cleared"]:
        rule = by_key[key]
        assert rule.condition(Facts(ordered, (), bare)) is True, key  # control: the gap fires
        assert rule.condition(Facts(ordered, guesses, bare)) is False, key
        assert rule.condition(Facts(ordered, (), with_quotes)) is False, key


def hand_row(company: str, ratings: str = "B2 / B+", bid: str = "98.5") -> dict[str, str]:
    return {
        "Company": company,
        "Borrower Name": f"{company} Holdings",
        "Bloomberg ID": f"ID-{company}-{ratings}-{bid}",
        "Loan Type": "B",
        "Ratings": ratings,
        "Bid": bid,
        "Ask": "99.5",
        "Mid YTM": "7.5",
        "Mid 3Y DM": "400",
    }


def test_issuer_selection_skips_a_company_with_a_dirty_tranche() -> None:
    rows = [
        hand_row("Aaa"),
        hand_row("Aaa", ratings="#N/A N/A / B+"),  # dirty Moody's part
        hand_row("Bbb", bid="#N/A N/A"),  # dirty Bid
        hand_row("Bbb"),
        hand_row("Ccc"),
        hand_row("Ccc", bid="97.0"),
        hand_row("Ddd"),
    ]
    chosen = synthetic_market_data.issuer_tranches(rows)
    assert {r["Company"] for r in chosen} == {"Ccc"}
    assert len(chosen) == 2


def test_issuer_selection_raises_when_no_company_qualifies() -> None:
    rows = [hand_row("Aaa"), hand_row("Bbb"), hand_row("Bbb", bid="#N/A N/A")]
    with pytest.raises(ValueError, match="two or more clean tranches"):
        synthetic_market_data.issuer_tranches(rows)
