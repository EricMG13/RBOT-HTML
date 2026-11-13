import contextlib
import io
from datetime import UTC, datetime

from test_signal_feeds import RSS

from deploy_workflow.signal.cli import main
from deploy_workflow.signal.feeds import Entry
from deploy_workflow.signal.fetch import Fetched, FetchRefused
from deploy_workflow.signal.identity import clean_name
from deploy_workflow.signal.store import add_story, open_db, propose_source, role_of


def run(tmp_path, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = main(["--root", str(tmp_path), *args])
    return code, out.getvalue()


def test_propose_approve_list(tmp_path, monkeypatch):
    monkeypatch.setattr("deploy_workflow.signal.cli.check_address", lambda url: None)
    assert (
        run(
            tmp_path,
            "sources",
            "propose",
            "Authority",
            "--kind",
            "regulator",
            "--url",
            "https://a.org/f",
            "--by",
            "ak",
        )[0]
        == 0
    )
    code, out = run(tmp_path, "sources", "list")
    assert code == 0 and "proposed" in out and "never checked" in out and "Authority" in out
    assert run(tmp_path, "sources", "approve", "1")[0] == 0
    assert "approved" in run(tmp_path, "sources", "list")[1]


def test_proposing_a_private_address_is_refused(tmp_path):
    code, out = run(
        tmp_path,
        "sources",
        "propose",
        "X",
        "--kind",
        "news",
        "--url",
        "https://127.0.0.1/f",
        "--by",
        "ak",
    )
    assert code == 2 and "plain host name" in out
    assert run(tmp_path, "sources", "list")[1].strip() == ""


def test_proposing_a_name_that_resolves_privately_is_refused(tmp_path, monkeypatch):
    monkeypatch.setattr("deploy_workflow.signal.fetch._resolve", lambda host: ["10.0.0.5"])
    code, out = run(
        tmp_path,
        "sources",
        "propose",
        "X",
        "--kind",
        "news",
        "--url",
        "https://feeds.example.org/f",
        "--by",
        "ak",
    )
    assert code == 2 and "public" in out
    assert run(tmp_path, "sources", "list")[1].strip() == ""


def test_invalid_role_exits_2(tmp_path):
    assert run(tmp_path, "users", "add", "X", "--role", "admin")[0] == 2


class _Clock(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 11, 13, 10, 0, tzinfo=tz)


def test_ingest_and_stories_with_recorded_feed(tmp_path, monkeypatch):
    monkeypatch.setattr("deploy_workflow.signal.cli.check_address", lambda url: None)
    monkeypatch.setattr("deploy_workflow.signal.cli.datetime", _Clock)
    monkeypatch.setattr(
        "deploy_workflow.signal.ingest.fetch.fetch", lambda u, e, m: Fetched(RSS, None, None)
    )
    run(
        tmp_path,
        "sources",
        "propose",
        "Authority",
        "--kind",
        "regulator",
        "--url",
        "https://a.org/f",
        "--by",
        "ak",
    )
    run(tmp_path, "sources", "approve", "1")
    code, out = run(tmp_path, "ingest")
    assert code == 0 and "2 new" in out
    code, out = run(tmp_path, "stories")
    # the undated item is shown with the fetch time (10:00), the dated one with its own time
    assert out.splitlines() == [
        "2026-11-13 10:00  Authority  No date",
        "2026-11-13 08:00  Authority  Authority opens review",
    ]


def test_sources_list_shows_why_a_source_is_failing(tmp_path, monkeypatch):
    monkeypatch.setattr("deploy_workflow.signal.cli.check_address", lambda url: None)

    def refuse(u, e, m):
        raise FetchRefused("server answered HTTP 503")

    monkeypatch.setattr("deploy_workflow.signal.ingest.fetch.fetch", refuse)
    run(
        tmp_path,
        "sources",
        "propose",
        "B",
        "--kind",
        "news",
        "--url",
        "https://b.org/f",
        "--by",
        "x",
    )
    run(tmp_path, "sources", "approve", "1")
    run(tmp_path, "ingest")
    out = run(tmp_path, "sources", "list")[1]
    assert "failing" in out and "server answered HTTP 503" in out


def test_story_count_of_others_counts_sources_not_links(tmp_path):
    db = open_db(tmp_path)
    for n in (1, 2):
        propose_source(db, f"S{n}", "news", f"https://s{n}.org/f", "x")
    t = datetime(2026, 11, 13, 9, tzinfo=UTC)
    title = "Authority opens in depth review"
    add_story(db, 1, Entry(title, "https://s1.org/1", t, ""), t)
    add_story(db, 2, Entry(title, "https://s2.org/1", t, ""), t)
    add_story(db, 2, Entry(title, "https://s2.org/2", t, ""), t)
    db.close()
    assert run(tmp_path, "stories")[1].splitlines() == [f"2026-11-13 09:00  S1  {title} (+1)"]


def test_approving_an_unknown_source_exits_2_with_one_line(tmp_path):
    code, out = run(tmp_path, "sources", "approve", "999")
    assert code == 2 and out.splitlines() == ["error: no source with id 999"]


def test_adding_a_user_with_an_empty_name_exits_2(tmp_path):
    code, out = run(tmp_path, "users", "add", "", "--role", "reader")
    assert code == 2 and out.splitlines() == ["error: display name is empty"]


def test_users_add_stores_the_name_the_page_looks_up(tmp_path):
    messy = "  B.   Novak "
    assert run(tmp_path, "users", "add", messy, "--role", "writer")[0] == 0
    db = open_db(tmp_path)
    try:
        assert role_of(db, clean_name(messy)) == "writer"
        assert [row["name"] for row in db.execute("SELECT name FROM users")] == ["B. Novak"]
    finally:
        db.close()


def test_users_add_refuses_a_name_that_cleans_to_nothing_in_one_line(tmp_path):
    code, out = run(tmp_path, "users", "add", "\u200b \t", "--role", "reader")
    assert code == 2 and out.splitlines() == ["error: display name is empty"]


def test_topics_add_and_list(tmp_path):
    assert (
        run(
            tmp_path,
            "topics",
            "add",
            "Competition",
            "--keywords",
            "merger review,remedy",
            "--by",
            "ak",
        )[0]
        == 0
    )
    code, out = run(tmp_path, "topics", "list")
    assert code == 0 and len(out.splitlines()) == 1 and "Competition" in out


def test_topic_with_no_keywords_exits_2_with_one_line(tmp_path):
    code, out = run(tmp_path, "topics", "add", "X", "--keywords", "", "--by", "ak")
    assert code == 2 and len(out.splitlines()) == 1


def test_kinds_with_spaces_after_commas_are_trimmed(tmp_path):
    code, _ = run(
        tmp_path,
        "topics",
        "add",
        "T",
        "--keywords",
        "review",
        "--kinds",
        "regulator, news",
        "--by",
        "ak",
    )
    assert code == 0
