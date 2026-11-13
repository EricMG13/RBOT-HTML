"""The Signal feed page in a real browser (headless Chrome) served by the real service on loopback.

Each test starts the service over the Task 2 feed fixture plus one hostile story, opens the page
as a reader would (`http://127.0.0.1:<port>/`; the service checks Host) and asserts on the live DOM.
Chrome is driven by `browser_signal_driver.cjs` (DevTools Protocol, real key presses and
clicks), the same way `browser_cdp_measure.cjs` serves the library tests; `chrome()` is the
library harness's.
Nothing is mocked. Needs Google Chrome or Chromium and node; skipped where Chrome is absent.

Screenshots go to a temporary folder; set SIGNAL_SHOT_DIR to a folder to keep them (that is how the
mockups under docs/design/mockups are refreshed).
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
from collections.abc import Callable, Iterator
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest
from test_library_page_browser import chrome
from test_signal_feedview import FETCHED, LAST, build_feed_db
from test_signal_service import Live

from deploy_workflow.signal.feeds import Entry
from deploy_workflow.signal.service import make_server
from deploy_workflow.signal.store import add_story, propose_source, set_source_state

pytestmark = pytest.mark.browser

DRIVER = Path(__file__).with_name("browser_signal_driver.cjs")
HOSTILE_TITLE = '<img src=x onerror="window.__xss=1">'
POLICY = (
    "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; "
    "img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; "
    "frame-ancestors 'none'"
)


@pytest.fixture(scope="module")
def chrome_path() -> str:
    return chrome()


def serve_site(root: Path, *, hostile: bool) -> Live:
    """The feed fixture (36 stories, topic Remedy) and, with `hostile`, a 37th story from a third
    approved source whose title is markup and whose link is a script URL, newest of all."""
    db = build_feed_db(root)
    try:
        if hostile:
            desk = propose_source(db, "Desk", "research", "https://d.org/f", "x")
            set_source_state(db, desk, "approved")
            entry = Entry(
                HOSTILE_TITLE,
                "javascript:window.__xss=1",
                LAST + timedelta(minutes=2),
                "Hostile summary",
            )
            assert add_story(db, desk, entry, FETCHED) == "new"
    finally:
        db.close()
    return Live(make_server(root, "127.0.0.1", 0))


@pytest.fixture
def site(tmp_path: Path) -> Iterator[Live]:
    live = serve_site(tmp_path / "hostile", hostile=True)
    yield live
    live.close()


@pytest.fixture
def plain_site(tmp_path: Path) -> Iterator[Live]:
    """No hostile story: its card has no Open source link, and the mockups should show real-looking
    stories."""
    live = serve_site(tmp_path / "plain", hostile=False)
    yield live
    live.close()


class Run:
    """What one driven browser session returned."""

    def __init__(self, raw: dict[str, Any], origin: str) -> None:
        self.values: dict[str, Any] = raw["values"]
        self.console: list[dict[str, str]] = raw["console"]
        self.requests: list[str] = raw["requests"]
        self.headers: list[dict[str, Any]] = raw["documentHeaders"]
        self.origin = origin

    def assert_quiet(self) -> None:
        """No console error or policy violation."""
        assert self.console == []

    def assert_same_origin(self) -> None:
        assert self.requests, "no request was recorded"
        # A data: URL (the policy's img-src allows it) is inline content, not a request to anyone.
        assert [u for u in self.requests if not u.startswith((self.origin + "/", "data:"))] == []


def drive(
    chrome_path: str,
    live: Live,
    steps: list[dict[str, Any]],
    *,
    width: int = 1280,
    on_stop: Callable[[], None] | None = None,
) -> Run:
    origin = f"http://127.0.0.1:{live.port}"
    job = {"url": origin + "/", "width": width, "height": 900, "steps": steps}
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8") as file:
        json.dump(job, file)
        file.flush()
        raw = run_node(chrome_path, Path(file.name), on_stop)
    return Run(raw, origin)


def run_node(chrome_path: str, job: Path, on_stop: Callable[[], None] | None) -> dict[str, Any]:
    proc = subprocess.Popen(
        ["node", str(DRIVER), chrome_path, str(job)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    watchdog = threading.Timer(100, proc.kill)
    watchdog.start()
    raw: dict[str, Any] | None = None
    try:
        assert proc.stdout is not None and proc.stdin is not None and proc.stderr is not None
        for line in proc.stdout:
            if line.startswith("@@STOP"):
                assert on_stop is not None, "the driver asked for a stop the test did not plan"
                on_stop()
                proc.stdin.write("go\n")
                proc.stdin.flush()
            elif line.startswith("@@RESULT "):
                raw = json.loads(line[len("@@RESULT ") :])
        err = proc.stderr.read()
        code = proc.wait()
    finally:
        watchdog.cancel()
        if proc.poll() is None:  # the watchdog fired or on_stop raised: let the driver clean up
            proc.terminate()  # its SIGTERM handler removes Chrome and the profile folder
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
    assert code == 0 and raw is not None, err
    return raw


# ----- steps and page expressions

BUSY_DONE = (
    "document.getElementById('feed').getAttribute('aria-busy') === 'false'"
    " && document.getElementById('skeleton').hidden"
)
SHOWN = (
    "(document.querySelectorAll('#cards article').length > 0"
    " || !document.getElementById('empty').hidden"
    " || !document.getElementById('error-band').hidden)"
)


def ready(title: str, cards: int | None = None) -> str:
    """The view `title` has finished loading (and shows `cards` cards, when given)."""
    count = (
        ""
        if cards is None
        else f" && document.querySelectorAll('#cards article').length === {cards}"
    )
    return (
        f"document.getElementById('view-title').textContent === {json.dumps(title)}"
        f" && {BUSY_DONE} && {SHOWN}{count}"
    )


def wait(expr: str, as_: str | None = None) -> dict[str, Any]:
    return {"wait": expr, **({"as": as_} if as_ else {})}


def look(name: str, expr: str) -> dict[str, Any]:
    return {"eval": expr, "as": name}


CARDS = "document.querySelectorAll('#cards article').length"
TITLES = "[...document.querySelectorAll('#cards article .headline')].map(h => h.textContent)"
PRESSED = "aria-pressed"
DIALOG_OPEN = "document.getElementById('name-dialog').open"

ENTER_NAME = [
    wait(DIALOG_OPEN),
    {"click": "#name-input"},
    {"insert": "A. Kovac"},
    {"click": "#name-form button[type=submit]"},
    wait(f"!{DIALOG_OPEN} && " + ready("For you")),
]


def view(name: str, title: str, cards: int | None = None) -> list[dict[str, Any]]:
    return [{"click": f'.ch[data-view="{name}"]'}, wait(ready(title, cards))]


# ----- tests


def test_first_visit_asks_for_a_name_and_a_reload_keeps_it(
    chrome_path: str, site: Live, tmp_path: Path
) -> None:
    run = drive(
        chrome_path,
        site,
        [
            wait(DIALOG_OPEN),
            look(
                "asked",
                "({open: " + DIALOG_OPEN + ", me: document.getElementById('me-name').textContent})",
            ),
            {"click": "#name-form button[type=submit]"},  # an empty name
            wait("!document.getElementById('name-error').hidden"),
            look(
                "refused",
                "({open: "
                + DIALOG_OPEN
                + ", error: document.getElementById('name-error').textContent})",
            ),
            {"click": "#name-input"},
            {"insert": "A. Kovac"},
            {"click": "#name-form button[type=submit]"},
            wait(f"!{DIALOG_OPEN} && " + ready("For you")),
            look(
                "chip",
                "({name: document.getElementById('me-name').textContent,"
                " role: document.getElementById('me-role').textContent,"
                " roleShown: !document.getElementById('me-role').hidden,"
                " initials: document.getElementById('me-initials').textContent})",
            ),
            {"reload": True},
            wait(
                "document.getElementById('me-name').textContent === 'A. Kovac' && "
                + ready("For you")
            ),
            look("again", DIALOG_OPEN),
        ],
    )
    assert run.values["asked"] == {"open": True, "me": "Set your name"}
    assert run.values["refused"] == {"open": True, "error": "Enter a name to continue."}
    chip = run.values["chip"]
    assert chip["name"] == "A. Kovac" and chip["initials"] == "AK" and chip["roleShown"] is True
    assert chip["role"].lower() == "reader"
    assert run.values["again"] is False  # the HttpOnly cookie kept the user
    run.assert_quiet()


def test_latest_pages_newest_first_and_the_hostile_story_is_inert(
    chrome_path: str, site: Live, tmp_path: Path
) -> None:
    run = drive(
        chrome_path,
        site,
        [
            *ENTER_NAME,
            *view("latest", "Latest", 30),
            look("first", TITLES + ".slice(0, 4)"),
            look("lastOfFirstPage", TITLES + "[29]"),
            look("moreShown", "!document.getElementById('more').hidden"),
            look(
                "hostile",
                "(() => { const a = document.querySelector('#cards article');"
                " return {title: a.querySelector('.headline').textContent,"
                " links: a.querySelectorAll('a').length,"
                " images: document.querySelectorAll('img').length,"
                " imagesInCards: document.querySelectorAll('#cards img').length,"
                " xss: String(window.__xss), save: !!a.querySelector('[data-action=save]')}; })()",
            ),
            {"click": "#more"},
            wait(f"{CARDS} === 37 && {BUSY_DONE}"),
            look("moreHidden", "document.getElementById('more').hidden"),
            look("all", TITLES + ".length"),
            look("lastTitle", TITLES + "[36]"),
        ],
    )
    values = run.values
    assert values["first"] == [HOSTILE_TITLE, "Wire piece on remedy", "Story 35", "Story 34"]
    assert values["lastOfFirstPage"] == "Story 08" and values["moreShown"] is True
    assert values["hostile"] == {
        "title": HOSTILE_TITLE,  # visible as text, not parsed as markup
        "links": 0,  # a script URL is no link
        "images": 0,
        "imagesInCards": 0,
        "xss": "undefined",
        "save": True,
    }
    assert values["all"] == 37 and values["lastTitle"] == "Story 01"
    assert values["moreHidden"] is True
    run.assert_quiet()
    run.assert_same_origin()
    assert not any(
        "/x" == u[len(run.origin) :] for u in run.requests
    )  # the img src was never fetched


def test_kind_chip_filters_and_search_is_debounced_and_cleared(
    chrome_path: str, site: Live, tmp_path: Path
) -> None:
    run = drive(
        chrome_path,
        site,
        [
            *ENTER_NAME,
            *view("latest", "Latest", 30),
            {"click": '#kind-chips [data-kind="news"]'},
            wait(f"{CARDS} === 1 && {BUSY_DONE}"),
            look(
                "news",
                "({titles: " + TITLES + ", pressed: document.querySelector('[data-kind=news]')"
                ".getAttribute('aria-pressed'), all: document.querySelector('[data-kind=\"\"]')"
                ".getAttribute('aria-pressed')})",
            ),
            {"click": '#kind-chips [data-kind=""]'},
            wait(ready("Latest", 30)),
            look("body", "String(document.activeElement === document.body)"),
            {"key": "/"},
            look(
                "slash",
                "({id: document.activeElement.id, value: document.getElementById('search').value})",
            ),
            look("typedAt", "performance.now()"),
            {"insert": "wire remedy"},
            look("beforeDebounce", CARDS),
            wait(f"{CARDS} === 1 && {BUSY_DONE}"),
            look("found", TITLES),
            look(
                "queryStart",
                "performance.getEntriesByType('resource').filter(e => e.name.includes('q=wire'))"
                ".map(e => e.startTime)",
            ),
            {"key": "Escape"},
            wait(f"{CARDS} === 30 && {BUSY_DONE}"),
            look("cleared", "document.getElementById('search').value"),
        ],
    )
    values = run.values
    assert values["news"] == {"titles": ["Wire piece on remedy"], "pressed": "true", "all": "false"}
    assert values["slash"] == {"id": "search", "value": ""}
    assert values["beforeDebounce"] == 30  # nothing is searched on the keystroke itself
    assert values["found"] == ["Wire piece on remedy"]
    assert len(values["queryStart"]) == 1
    assert values["queryStart"][0] - values["typedAt"] >= 290  # the 300 ms debounce
    assert values["cleared"] == ""
    run.assert_quiet()
    run.assert_same_origin()


def test_save_toggles_and_the_story_is_listed_under_saved_after_a_reload(
    chrome_path: str, site: Live, tmp_path: Path
) -> None:
    second = "#cards article:nth-child(2)"
    run = drive(
        chrome_path,
        site,
        [
            *ENTER_NAME,
            *view("latest", "Latest", 30),
            look(
                "before",
                f"document.querySelector('{second} [data-action=save]').getAttribute('{PRESSED}')",
            ),
            look("id", f"document.querySelector('{second}').getAttribute('data-id')"),
            {"click": f"{second} [data-action=save]"},
            wait(
                f"document.querySelector('{second} [data-action=save]')"
                f".getAttribute('{PRESSED}') === 'true'"
            ),
            {"reload": True},
            wait(
                "document.getElementById('me-name').textContent === 'A. Kovac' && "
                + ready("For you")
            ),
            *view("saved", "Saved", 1),
            look("saved", TITLES),
            look("savedId", "document.querySelector('#cards article').getAttribute('data-id')"),
            look(
                "pressed",
                "document.querySelector('#cards [data-action=save]').getAttribute('aria-pressed')",
            ),
            {"click": "#cards [data-action=save]"},  # and off again
            wait(
                "document.querySelector('#cards [data-action=save]').getAttribute('aria-pressed')"
                " === 'false'"
            ),
        ],
    )
    values = run.values
    assert values["before"] == "false"
    assert values["saved"] == ["Wire piece on remedy"]
    assert values["savedId"] == values["id"] and values["pressed"] == "true"
    run.assert_quiet()


def test_following_a_topic_fills_for_you_and_keeps_keyboard_focus(
    chrome_path: str, site: Live, tmp_path: Path
) -> None:
    follow = '#topic-list [data-follow="1"]'
    run = drive(
        chrome_path,
        site,
        [
            *ENTER_NAME,
            look("empty", "document.getElementById('empty').textContent"),
            look("emptyCards", CARDS),
            look(
                "pressedBefore", f"document.querySelector('{follow}').getAttribute('aria-pressed')"
            ),
            {"eval": f"document.querySelector('{follow}').focus()", "as": "focused"},
            {"key": "Enter"},
            wait(f"{CARDS} === 1 && {BUSY_DONE}"),
            look(
                "after",
                "({pressed: [...document.querySelectorAll('[data-follow=\"1\"]')]"
                ".map(b => b.getAttribute('aria-pressed')),"
                " focus: document.activeElement.getAttribute('data-follow'),"
                " inChannels: !!document.activeElement.closest('#channels'),"
                " titles: " + TITLES + "})",
            ),
            {"reload": True},
            wait(
                "document.getElementById('me-name').textContent === 'A. Kovac' && "
                + ready("For you", 1)
            ),
            look("persisted", TITLES),
        ],
    )
    values = run.values
    assert "Follow a topic to fill this view" in values["empty"] and values["emptyCards"] == 0
    assert values["pressedBefore"] == "false"
    after = values["after"]
    assert (
        after["focus"] == "1" and after["inChannels"] is True
    )  # still on the topic's follow button
    assert after["pressed"] == ["true"] * len(after["pressed"]) and after["pressed"]
    assert after["titles"] == ["Wire piece on remedy"]
    assert values["persisted"] == ["Wire piece on remedy"]
    run.assert_quiet()


def test_a_stopped_service_shows_the_error_band_and_keeps_the_cards(
    chrome_path: str, site: Live, tmp_path: Path
) -> None:
    run = drive(
        chrome_path,
        site,
        [
            *ENTER_NAME,
            *view("latest", "Latest", 30),
            look("before", TITLES),
            {"stop": True},
            {"click": '.ch[data-view="saved"]'},
            wait("!document.getElementById('error-band').hidden"),
            look(
                "band",
                "({text: document.getElementById('error-text').textContent,"
                " retry: document.getElementById('retry').textContent,"
                " retryShown: document.getElementById('retry').offsetParent !== null,"
                " cards: " + TITLES + "})",
            ),
        ],
        on_stop=lambda: site.close(),
    )
    band = run.values["band"]
    assert band["retry"] == "Retry" and band["retryShown"] is True
    assert band["text"] == "Signal could not be reached. Check your connection and try again."
    assert band["cards"] == run.values["before"] and len(band["cards"]) == 30  # the cards stay
    # The refused connection is the browser's own network message; nothing else may be reported.
    assert run.console and all(line["source"] == "network" for line in run.console), run.console
    run.assert_same_origin()


def test_a_plain_visit_logs_nothing(chrome_path: str, site: Live, tmp_path: Path) -> None:
    run = drive(chrome_path, site, [*ENTER_NAME, *view("latest", "Latest", 30)])
    assert run.console == []


def test_the_policy_is_exact_and_the_page_asks_for_nothing_from_elsewhere(
    chrome_path: str, site: Live, tmp_path: Path
) -> None:
    run = drive(
        chrome_path,
        site,
        [
            *ENTER_NAME,
            *view("latest", "Latest", 30),
            {"click": "#more"},
            wait(f"{CARDS} === 37 && {BUSY_DONE}"),
        ],
    )
    page = [h for h in run.headers if h["url"] == run.origin + "/"]
    assert len(page) == 1
    policy = {k.lower(): v for k, v in page[0]["headers"].items()}["content-security-policy"]
    assert policy == POLICY and "unsafe-inline" not in policy
    run.assert_same_origin()
    assert any(u.startswith(run.origin + "/api/feed") for u in run.requests)
    run.assert_quiet()  # no policy violation was logged


CONTRAST = """(() => {
  const parse = c => {
    const m = c.match(/rgba?\\(([^)]+)\\)/).slice(1)[0].split(/[ ,\\/]+/).map(Number);
    return {r: m[0], g: m[1], b: m[2], a: m.length > 3 ? m[3] : 1}; };
  const over = (top, under) => ({r: top.r * top.a + under.r * (1 - top.a),
    g: top.g * top.a + under.g * (1 - top.a), b: top.b * top.a + under.b * (1 - top.a), a: 1});
  const lum = c => {
    const f = v => {
      v /= 255;
      return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    };
    return 0.2126 * f(c.r) + 0.7152 * f(c.g) + 0.0722 * f(c.b); };
  const ratio = (a, b) => {
    const x = lum(a), y = lum(b);
    return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05);
  };
  const background = el => {
    let layers = [];
    for (let e = el; e; e = e.parentElement) {
      const s = getComputedStyle(e);
      if (s.backgroundImage !== 'none') layers.push('image:' + e.className);
      const c = parse(s.backgroundColor);
      if (c.a > 0) { layers.push(c); if (c.a === 1) break; }
    }
    const shown = layers.filter(l => typeof l !== 'string');
    let base = {r: 255, g: 255, b: 255, a: 1};
    for (const l of shown.reverse()) base = over(l, base);
    return {base, images: layers.filter(l => typeof l === 'string')};
  };
  const opacity = el => {
    let o = 1;
    for (let e = el; e; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity);
    return o;
  };
  const cards = [...document.querySelectorAll('#cards article')].slice(0, 3);
  const roots = cards.concat([document.getElementById('channels')]);
  const out = [];
  for (const root of roots) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const seen = new Set();
    while (walker.nextNode()) {
      const node = walker.currentNode, el = node.parentElement;
      if (!node.data.trim() || seen.has(el)) continue;
      seen.add(el);
      const s = getComputedStyle(el), box = el.getBoundingClientRect();
      const hidden = s.visibility === 'hidden' || s.display === 'none' || opacity(el) === 0;
      if (hidden || box.width === 0 || box.height === 0) continue;
      const bg = background(el), o = opacity(el), fg = parse(s.color);
      const text = over({...fg, a: fg.a * o}, bg.base);
      out.push({text: node.data.trim().slice(0, 40), root: root.id || 'card',
        ratio: ratio(text, bg.base), size: s.fontSize, images: bg.images});
    }
  }
  return out;
})()"""


def test_text_in_the_first_cards_and_the_channel_list_has_enough_contrast(
    chrome_path: str, site: Live, tmp_path: Path
) -> None:
    run = drive(
        chrome_path,
        site,
        [*ENTER_NAME, *view("latest", "Latest", 30), look("contrast", CONTRAST)],
    )
    measured = run.values["contrast"]
    roots = {m["root"] for m in measured}
    assert roots == {"card", "channels"}
    assert (
        sum(m["root"] == "card" for m in measured) >= 3 * 4
    )  # kind, headline, meta, acts per card
    assert [m for m in measured if m["images"]] == []  # a background image would defeat the measure
    weak = [(m["text"], round(m["ratio"], 2)) for m in measured if m["ratio"] < 4.5]
    assert weak == []
    run.assert_quiet()


DESCRIBE = """(() => {
  // A control may show its focus on a wrapper that has focus within (the search field does).
  const ring = e => { for (let a = e.parentElement; a && a !== document.body; a = a.parentElement) {
    const s = getComputedStyle(a);
    if (a.matches(':focus-within') && s.outlineStyle !== 'none' && parseFloat(s.outlineWidth) > 0)
      return a.className; }
    return ''; };
  const e = document.activeElement, s = getComputedStyle(e), card = e.closest('article');
  return {tag: e.tagName.toLowerCase(), id: e.id, cls: String(e.getAttribute('class') || ''),
    text: (e.getAttribute('aria-label') || e.textContent).trim().slice(0, 50),
    card: card ? Array.prototype.indexOf.call(card.parentNode.children, card) : null,
    action: e.getAttribute('data-action'), inChannels: !!e.closest('#channels'),
    outline: [s.outlineStyle, s.outlineWidth], shadow: s.boxShadow, wrapper: ring(e)};
})()"""
TABS = 22


def test_keyboard_alone_reaches_the_controls_in_order_with_a_visible_focus(
    chrome_path: str, plain_site: Live, tmp_path: Path
) -> None:
    # Without the hostile story: its card has no Open source link, and the first card must have one.
    steps: list[dict[str, Any]] = [
        *ENTER_NAME,
        {"reload": True},  # a fresh document, so Tab starts at the top
        wait(
            "document.getElementById('me-name').textContent === 'A. Kovac' && " + ready("For you")
        ),
        look(
            "toggleDisplay", "getComputedStyle(document.getElementById('channels-toggle')).display"
        ),
        {"click": '.ch[data-view="latest"]'},
        wait(ready("Latest", 30)),
        look(
            "blur",
            "(() => { const b = document.body; b.setAttribute('tabindex', '-1'); b.focus();"
            " b.removeAttribute('tabindex'); window.scrollTo(0, 0);"
            " return document.activeElement.tagName; })()",
        ),
    ]
    for n in range(TABS):
        steps += [{"key": "Tab"}, look(f"t{n}", DESCRIBE)]
    run = drive(chrome_path, plain_site, steps)
    stops = [run.values[f"t{n}"] for n in range(TABS)]
    assert run.values["toggleDisplay"] == "none"  # at 1280 px there is no Channels button
    wanted: list[tuple[str, Callable[[dict[str, Any]], bool]]] = [
        ("skip link", lambda s: "skip-link" in s["cls"]),
        ("a channel-list button", lambda s: s["inChannels"] and s["tag"] == "button"),
        ("the search field", lambda s: s["id"] == "search"),
        ("the first card's Save", lambda s: s["card"] == 0 and s["action"] == "save"),
        ("the first card's Open source", lambda s: s["card"] == 0 and "act open" in s["cls"]),
    ]
    at = -1
    reached: list[dict[str, Any]] = []
    for label, test in wanted:
        found = next((i for i in range(at + 1, len(stops)) if test(stops[i])), None)
        assert found is not None, (label, stops)
        at = found
        reached.append(stops[at])
    for stop in stops[: at + 1]:
        outlined = stop["outline"][0] != "none" and float(stop["outline"][1].removesuffix("px")) > 0
        assert outlined or stop["shadow"] != "none" or stop["wrapper"], stop
    run.assert_quiet()


def test_at_375_px_nothing_scrolls_sideways_and_channels_open_from_a_button(
    chrome_path: str, plain_site: Live, tmp_path: Path
) -> None:
    shown = "(e => { const s = getComputedStyle(e), r = e.getBoundingClientRect();"
    shown += " return s.display !== 'none' && s.visibility !== 'hidden'"
    shown += " && r.right > 0 && r.left < innerWidth; })"
    channels = f"{shown}(document.getElementById('channels'))"
    shot = shot_path(tmp_path, "signal-slice2-latest-375.png")
    run = drive(
        chrome_path,
        plain_site,
        [
            *ENTER_NAME,
            look("closed", channels),
            look(
                "toggle",
                "({shown: getComputedStyle(document.getElementById('channels-toggle')).display,"
                " text: document.getElementById('channels-toggle').textContent.trim(),"
                " expanded: document.getElementById('channels-toggle')"
                ".getAttribute('aria-expanded')})",
            ),
            {"click": "#channels-toggle"},
            wait(channels),
            look(
                "opened", "document.getElementById('channels-toggle').getAttribute('aria-expanded')"
            ),
            *view("latest", "Latest", 30),  # choosing a view closes the list
            look("closedAgain", channels),
            look(
                "widths",
                "[document.documentElement.scrollWidth, document.documentElement.clientWidth,"
                " innerWidth]",
            ),
            {"shot": str(shot)},
            {"click": "#channels-toggle"},
            wait(channels),
            {"eval": "document.querySelector('.ch[data-view=\"saved\"]').focus()", "as": "focus"},
            {"key": "Escape"},
            wait(f"!{channels}"),
            look(
                "afterEscape",
                "({id: document.activeElement.id,"
                " expanded: document.getElementById('channels-toggle')"
                ".getAttribute('aria-expanded')})",
            ),
        ],
        width=375,
    )
    values = run.values
    assert values["closed"] is False and values["closedAgain"] is False
    assert values["toggle"] == {"shown": "flex", "text": "Channels", "expanded": "false"}
    assert values["opened"] == "true"
    scroll, client, inner = values["widths"]
    assert inner == 375 and scroll <= 375 and client <= 375, values["widths"]
    assert values["afterEscape"] == {"id": "channels-toggle", "expanded": "false"}
    run.assert_quiet()
    assert_png(shot, 375)


def shot_path(tmp_path: Path, name: str) -> Path:
    keep = os.environ.get("SIGNAL_SHOT_DIR")
    folder = Path(keep) if keep else tmp_path
    folder.mkdir(parents=True, exist_ok=True)
    return folder / name


def assert_png(path: Path, width: int) -> None:
    head = path.read_bytes()[:24]
    assert head[:8] == b"\x89PNG\r\n\x1a\n"
    assert int.from_bytes(head[16:20], "big") == width


def test_screenshots_of_the_real_page_at_1280(
    chrome_path: str, plain_site: Live, tmp_path: Path
) -> None:
    empty = shot_path(tmp_path, "signal-slice2-foryou-empty-1280.png")
    latest = shot_path(tmp_path, "signal-slice2-latest-1280.png")
    run = drive(
        chrome_path,
        plain_site,
        [
            *ENTER_NAME,
            look("emptyText", "document.getElementById('empty').textContent"),
            {"shot": str(empty)},
            *view("latest", "Latest", 30),
            {"shot": str(latest)},
        ],
    )
    assert "Follow a topic to fill this view" in run.values["emptyText"]
    run.assert_quiet()
    assert_png(empty, 1280)
    assert_png(latest, 1280)
