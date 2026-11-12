"""The HTML Model's brand tokens and chart rules (static): values are the brand answer key, and
bright chart fills never land on thin strokes or text."""

import re
from pathlib import Path

ASSETS = Path(__file__).resolve().parents[1] / "src/deploy_vii/assets"
TOKENS = {
    "rb-navy": "#000533",
    "rb-blue": "#001AFF",
    "rb-blue-hover": "#0012B2",
    "rb-logo-field": "#001AFF",
    "rb-ground": "#F4F4F5",
    "rb-head": "#FAFAFB",
    "rb-rule": "#E8E9EB",
    "rb-rule-soft": "#F4F4F5",
    "rb-select": "#E5E8FF",
    "rb-ink": "#000533",
    "rb-ink-2": "#383B3F",
    "rb-ink-3": "#63676E",
    "rb-pos": "#0F8048",
    "rb-pos-tint": "#E8FFF4",
    "rb-caut": "#806300",
    "rb-caut-tint": "#FFF4CC",
    "rb-neg": "#8E413E",
    "rb-neg-tint": "#FDF0F0",
    "rb-neu": "#474A4F",
    "rb-neu-tint": "#F4F4F5",
    "rb-ch-1": "#001AFF",
    "rb-ch-2": "#1EFF8F",
    "rb-ch-3": "#EAFF00",
    "rb-ch-4": "#A29AFF",
    "rb-ch-5": "#256A80",
    "rb-ch-1-ln": "#001AFF",
    "rb-ch-2-ln": "#0F8048",
    "rb-ch-3-ln": "#758000",
    "rb-ch-4-ln": "#514D80",
    "rb-ch-5-ln": "#256A80",
    "rb-ch-grid": "#E8E9EB",
    "rb-ch-track": "#F4F4F5",
}

HEX = r"#[0-9a-fA-F]{3,8}\b(?=[;\s,)}!])"


def declarations() -> dict[str, str]:
    text = re.sub(
        r"/\*.*?\*/", "", (ASSETS / "tokens.css").read_text(encoding="utf-8"), flags=re.DOTALL
    )
    return {name: value.strip() for name, value in re.findall(r"--([\w-]+):\s*([^;]+);", text)}


def rules() -> list[tuple[str, str]]:
    text = re.sub(
        r"/\*.*?\*/", "", (ASSETS / "app.css").read_text(encoding="utf-8"), flags=re.DOTALL
    )
    return re.findall(r"([^{}]+)\{([^{}]*)\}", text)


def test_tokens_have_the_brand_values():
    found = declarations()
    wrong = {n: (found.get(n), v) for n, v in TOKENS.items() if (found.get(n) or "").upper() != v}
    assert wrong == {}


def test_app_css_has_no_literal_hex():
    assert re.findall(HEX, (ASSETS / "app.css").read_text()) == []


def test_no_rule_strokes_with_a_bright_fill():
    bare = [
        (sel.strip(), body)
        for sel, body in rules()
        if re.search(r"stroke:\s*var\(--rb-ch-[234]\)", body)
    ]
    assert bare == []


def test_chart_text_carrying_a_series_fill_uses_the_line_token():
    for n in (1, 2, 4, 5):  # series 3 is ruled to ink: test_series_three_labels_are_ink
        matches = [
            body
            for sel, body in rules()
            if any(s.strip() == f".chart text.f{n}" for s in sel.split(","))
        ]
        assert matches, f"no rule for chart text carrying f{n}"
        assert f"fill:var(--rb-ch-{n}-ln)" in matches[-1].replace(" ", "")


def _body(selector: str) -> str:
    matches = [
        body.replace(" ", "")
        for sel, body in rules()
        if any(s.strip() == selector for s in sel.split(","))
    ]
    assert matches, f"no rule for {selector}"
    return matches[-1]


def test_hatch_stripes_use_the_line_token():
    for n in range(1, 6):
        assert f"fill:var(--rb-ch-{n}-ln)" in _body(f".chart pattern rect.f{n}")


def test_waterfall_steps_use_the_brief_tokens():
    expected = {
        "wf-up": "fill:var(--rb-ch-1);stroke:var(--rb-ch-1-ln)",
        "wf-down": "fill:var(--rb-ch-5);stroke:var(--rb-ch-5-ln)",
        "wf-total": "fill:var(--rb-navy);stroke:var(--rb-navy)",
        "wf-residual": "fill:var(--rb-neg);stroke:var(--rb-neg)",
    }
    for name, decl in expected.items():
        assert _body(f".chart .{name}").rstrip(";") == decl


def test_no_text_rule_gets_a_bare_bright_fill():
    bad = [
        sel.strip()
        for sel, body in rules()
        for s in sel.split(",")
        if re.search(r"(?:\btext\b|\.lb\b)", s) and re.search(r"fill:\s*var\(--rb-ch-[234]\)", body)
    ]
    assert bad == []


def test_legend_swatches_carry_an_inset_line_edge():
    for n in range(1, 6):
        want = f"background:var(--rb-ch-{n});box-shadow:inset0001pxvar(--rb-ch-{n}-ln)"
        assert _body(f".sw{n}").rstrip(";") == want


def test_series_three_labels_are_ink():
    assert "fill:var(--rb-ink)" in _body(".chart text.f3")


def test_hex_followed_by_important_is_caught():
    assert re.search(HEX, "a{color:#fff!important}")
