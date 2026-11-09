"""Contracts the paper's numbers depend on: link parsing, session splitting and order statistics."""
from datetime import datetime, timedelta, timezone

from breadcrumbs.analysis import ascending_share, longest_run
from breadcrumbs.data import extract_links, sessions


def test_links_count_bracket_and_bare_wiki_words_but_only_known_titles():
    titles = {"ZZZDataUSAConstructionWageLive", "AgentBridgeTest", "OtherPage"}
    body = ("If this page vanishes, try [[ZZZDataUSAConstructionWageLive]]. "
            "See AgentBridgeTest or [[Missing Page]]; plain words like Hello stay out. xAgentBridgeTestx")
    assert extract_links(body, titles) == {"ZZZDataUSAConstructionWageLive", "AgentBridgeTest"}


def test_sessions_split_on_gaps_longer_than_threshold():
    t0 = datetime(2026, 6, 19, tzinfo=timezone.utc)
    times = [t0, t0 + timedelta(minutes=29), t0 + timedelta(minutes=60), t0 + timedelta(minutes=200)]
    assert sessions(times, 30) == [(0, 2), (2, 3), (3, 4)]
    assert sessions(times, 120) == [(0, 3), (3, 4)]


def test_order_statistics_are_case_insensitive():
    titles = ["alpha", "Beta", "charlie", "Alpha2", "delta"]
    assert ascending_share(titles) == 3 / 4
    assert longest_run(titles) == 3
