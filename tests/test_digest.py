from mcp_nhl.digest import _fmt_plus_minus, _game_line, format_players_digest


def test_fmt_plus_minus():
    assert _fmt_plus_minus(3) == "+3"
    assert _fmt_plus_minus(0) == "0"
    assert _fmt_plus_minus(-2) == "-2"


def test_game_line_forward_with_box():
    game = {"gameDate": "2026-04-15", "homeRoadFlag": "R", "opponentAbbrev": "FLA",
            "goals": 1, "assists": 2, "points": 3, "plusMinus": 1, "shots": 4}
    box = {"toi": "18:41", "sog": 5, "faceoffPct": 55.0, "hits": 2, "blocks": 1}
    line = _game_line(game, box, "C")
    assert "A vs FLA" in line
    assert "1G 2A (3P)" in line
    assert "+1" in line
    assert "SOG 5" in line
    assert "FO 55.0%" in line
    assert "TOI 18:41" in line
    assert "hits 2 / blocks 1" in line


def test_game_line_defenseman_suppresses_faceoff():
    game = {"gameDate": "d", "homeRoadFlag": "H", "opponentAbbrev": "NYI",
            "goals": 0, "assists": 1, "points": 1, "plusMinus": -1}
    box = {"toi": "15:00", "sog": 1, "faceoffPct": 0.0}
    assert "FO -" in _game_line(game, box, "D")


def test_game_line_without_box_falls_back_to_gamelog_fields():
    game = {"gameDate": "d", "homeRoadFlag": "H", "opponentAbbrev": "NYI",
            "goals": 0, "assists": 0, "points": 0, "plusMinus": 0,
            "shots": 2, "toi": "11:17"}
    line = _game_line(game, None, "C")
    assert "SOG 2" in line and "TOI 11:17" in line and "FO -" in line


def test_digest_numeric_id_full_block(client):
    out = format_players_digest([8482079], games=2, boxscore=False, client=client)
    assert out.startswith("# NHL player digest")
    assert "1 players, last 2 games" in out
    assert "Marco Rossi" in out           # from player_landing.json fixture
    assert "Season 20252026" in out
    assert "Last 2 games:" in out


def test_digest_no_games_branch(client, monkeypatch):
    monkeypatch.setattr(client, "player_gamelog", lambda *a, **k: {"gameLog": []})
    out = format_players_digest([8482079], client=client)
    assert "No NHL games this season" in out


def test_digest_name_mismatch_correction(client, monkeypatch):
    # A stale id resolves to the wrong person: landing fixture says "Rossi" but
    # we asked for "Sidney Crosby". The guard re-resolves via search (fixture
    # returns a different id) and flags the correction.
    monkeypatch.setattr(client, "resolve_player", lambda *a, **k: 9999999)
    out = format_players_digest(["Sidney Crosby"], games=1, boxscore=False, client=client)
    assert "id corrected to" in out


def test_digest_clamps_games(client):
    out = format_players_digest([8482079], games=999, boxscore=False, client=client)
    assert "last 20 games" in out
