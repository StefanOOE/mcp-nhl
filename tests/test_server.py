"""Server-level checks: every tool is registered, and the tools that need
argument validation reject bad input. Network is stubbed via the shared
FakeOpener on the module-level client."""

from __future__ import annotations

import asyncio
import inspect

import pytest

import mcp_nhl.server as srv
from mcp_nhl.client import NHLAPIError, NHLClient

EXPECTED_TOOLS = {
    "search_players", "player_summary", "player_gamelog", "player_spotlight",
    "players_digest", "daily_scores", "scoreboard", "game_boxscore",
    "game_play_by_play", "game_landing", "game_story", "team_roster",
    "team_prospects", "team_schedule", "team_stats", "team_scoreboard",
    "standings", "standings_seasons", "league_schedule", "schedule_calendar",
    "skater_leaders", "goalie_leaders", "playoff_bracket",
    "playoff_series_schedule", "playoff_carousel", "draft_rankings",
    "draft_picks", "draft_tracker", "seasons", "meta", "stats_report",
    "nhl_api_get",
}


def _list_tools():
    result = srv.mcp.list_tools()
    if inspect.iscoroutine(result):
        result = asyncio.run(result)
    return list(result)


@pytest.fixture(autouse=True)
def stub_client(fake_opener, monkeypatch):
    c = NHLClient(opener=fake_opener, retries=0)
    c._season_cache = "20252026"
    monkeypatch.setattr(srv, "_client", c)
    return c


def test_all_tools_registered():
    names = {t.name for t in _list_tools()}
    assert EXPECTED_TOOLS <= names, EXPECTED_TOOLS - names


def test_tools_have_descriptions():
    for t in _list_tools():
        assert t.description and len(t.description) > 15, t.name


def test_players_digest_tool_returns_text(stub_client):
    out = srv.players_digest(["Marco Rossi"], games=1, boxscore=False)
    assert isinstance(out, str) and "Marco Rossi" in out


def test_game_boxscore_player_filter(stub_client):
    res = srv.game_boxscore(2024020600, player="8478444")
    assert res["playerId"] == 8478444
    assert res["stats"]["sog"] == 5


def test_nhl_api_get_passthrough_allowlist(stub_client):
    with pytest.raises(NHLAPIError):
        srv.nhl_api_get("https://example.org/x")


def test_stats_report_validates_entity(stub_client):
    with pytest.raises(NHLAPIError):
        srv.stats_report(entity="zamboni")
