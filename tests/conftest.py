"""Offline test doubles: a fake urllib opener that serves recorded fixtures
based on the request URL, with no network access."""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path

import pytest

from mcp_nhl.client import NHLClient

FIXTURES = Path(__file__).parent / "fixtures"

# Substring in the URL -> fixture file. First match wins.
ROUTES: list[tuple[str, str]] = [
    ("search.d3.nhle.com", "search_player.json"),
    ("/landing", "player_landing.json"),
    ("/game-log/now", "player_gamelog_now.json"),
    ("/game-log/", "player_gamelog_now.json"),
    ("/gamecenter/", "boxscore.json"),
    ("/score/", "score_date.json"),
    ("/standings/", "standings_now.json"),
    ("/roster/", "roster_current.json"),
    ("/schedule/", "schedule_now.json"),
    ("skater-stats-leaders", "skater_leaders.json"),
    ("/v1/season", "seasons.json"),
    ("stats/rest", "stats_skater_summary.json"),
]


class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


class FakeOpener:
    """Drop-in for urllib.request.OpenerDirector."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.force_status: int | None = None

    def open(self, req, timeout=None):  # noqa: ARG002
        url = req.full_url if hasattr(req, "full_url") else str(req)
        self.calls.append(url)
        if self.force_status:
            raise urllib.error.HTTPError(url, self.force_status, "forced", {}, None)
        for needle, fixture in ROUTES:
            if needle in url:
                return _Resp((FIXTURES / fixture).read_bytes())
        raise urllib.error.HTTPError(url, 404, "no fixture", {}, None)


@pytest.fixture
def fake_opener() -> FakeOpener:
    return FakeOpener()


@pytest.fixture
def client(fake_opener: FakeOpener) -> NHLClient:
    c = NHLClient(opener=fake_opener, retries=0)
    c._season_cache = "20252026"
    return c


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())
