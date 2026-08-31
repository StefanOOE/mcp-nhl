import pytest

from mcp_nhl.client import NHLAPIError, NHLClient, _localized


def test_localized():
    assert _localized({"default": "Red Wings"}) == "Red Wings"
    assert _localized("plain") == "plain"
    assert _localized(None) == ""
    assert _localized(5) == "5"


def test_get_builds_url_with_params(client, fake_opener):
    client.skater_leaders(categories="goals", limit=3)
    url = fake_opener.calls[-1]
    assert url.startswith("https://api-web.nhle.com/v1/skater-stats-leaders/current?")
    assert "categories=goals" in url and "limit=3" in url


def test_get_omits_none_params(client, fake_opener):
    client.skater_leaders(limit=5)
    assert "categories=" not in fake_opener.calls[-1]


def test_http_404_raises(client, fake_opener):
    fake_opener.force_status = 404
    with pytest.raises(NHLAPIError):
        client.standings()


def test_retry_then_success(monkeypatch):
    calls = {"n": 0}

    class Flaky:
        def open(self, req, timeout=None):
            calls["n"] += 1
            if calls["n"] == 1:
                raise OSError("connection reset")
            import io
            return io.BytesIO(b'[20242025, 20252026]')

    c = NHLClient(opener=Flaky(), retries=1)
    monkeypatch.setattr("time.sleep", lambda *_: None)
    assert c.seasons() == [20242025, 20252026]
    assert calls["n"] == 2


def test_resolve_player_numeric_passthrough(client, fake_opener):
    assert client.resolve_player(8482079) == 8482079
    assert client.resolve_player("8483464") == 8483464
    assert fake_opener.calls == []  # no search needed


def test_resolve_player_by_name(client, fake_opener):
    pid = client.resolve_player("McDavid")
    assert isinstance(pid, int) and pid > 0
    assert "search.d3.nhle.com" in fake_opener.calls[-1]


def test_current_season_cached(client, fake_opener):
    client._season_cache = None
    assert client.current_season() == "20262027"  # max of seasons.json
    n = len(fake_opener.calls)
    client.current_season()
    assert len(fake_opener.calls) == n  # cached, no second call


def test_player_gamelog_now_vs_season(client, fake_opener):
    client.player_gamelog(8483464)
    assert fake_opener.calls[-1].endswith("/game-log/now")
    client.player_gamelog(8483464, season="20242025", game_type=3)
    assert fake_opener.calls[-1].endswith("/game-log/20242025/3")


def test_team_schedule_span_validation(client):
    with pytest.raises(NHLAPIError):
        client.team_schedule("EDM", span="decade")


def test_team_code_uppercased(client, fake_opener):
    client.team_roster("edm")
    assert "/roster/EDM/current" in fake_opener.calls[-1]


def test_player_boxscore_stats_extracts_one_skater(client):
    # Boeser (8478444) is in boxscore.json awayTeam forwards
    line = client.player_boxscore_stats(2024020600, 8478444)
    assert line["sog"] == 5
    assert line["faceoffPct"] == 0.0
    assert line["toi"] == "18:17"


def test_player_boxscore_stats_missing_player(client):
    assert client.player_boxscore_stats(2024020600, 1) is None


def test_stats_report_default_cayenne(client, fake_opener):
    client.stats_report(entity="skater", report="summary")
    url = fake_opener.calls[-1]
    assert "api.nhle.com/stats/rest/en/skater/summary" in url
    assert "seasonId%3D20252026" in url or "seasonId=20252026" in url


def test_stats_report_bad_entity(client):
    with pytest.raises(NHLAPIError):
        client.stats_report(entity="referee")


def test_passthrough_rejects_foreign_host(client):
    with pytest.raises(NHLAPIError):
        client.passthrough("https://evil.example.com/v1/score/now")


def test_passthrough_v1_path(client, fake_opener):
    client.passthrough("/v1/standings/now")
    assert fake_opener.calls[-1] == "https://api-web.nhle.com/v1/standings/now"


def test_passthrough_stats_path(client, fake_opener):
    client.passthrough("stats/en/skater/summary", {"limit": 1})
    url = fake_opener.calls[-1]
    assert url.startswith("https://api.nhle.com/stats/rest/en/skater/summary?")
