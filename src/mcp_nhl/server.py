"""MCP server exposing the public NHL APIs as tools.

Run with ``python -m mcp_nhl`` (stdio transport).
"""

from __future__ import annotations

from typing import Any

from mcp.server import MCPServer

from .client import NHLClient
from .digest import format_players_digest

mcp = MCPServer(
    "mcp-nhl",
    version="0.1.0",
    instructions=(
        "Read-only access to the public NHL APIs (api-web.nhle.com and "
        "api.nhle.com/stats/rest). No API key. Player arguments accept either a "
        "full name or a numeric NHL player id. Season ids are 8 digits, e.g. "
        "20252026. Game type 2 = regular season, 3 = playoffs. For endpoints "
        "not wrapped by a dedicated tool, use nhl_api_get."
    ),
)

_client = NHLClient()


# --- players -----------------------------------------------------------

@mcp.tool()
def search_players(query: str, limit: int = 10, active_only: bool = False) -> list[dict]:
    """Search players by name. Returns playerId, name, position, team, active."""
    return _client.search_players(query, limit=limit, active_only=active_only)


@mcp.tool()
def player_summary(player: str | int) -> dict:
    """Full player landing page: bio, current team, featured season stats,
    career totals and the last 5 games. ``player`` is a name or numeric id."""
    return _client.player_landing(player)


@mcp.tool()
def player_gamelog(player: str | int, season: str | int | None = None,
                   game_type: int = 2, limit: int = 10) -> list[dict]:
    """Game-by-game log for a player. Omit ``season`` for the current one."""
    data = _client.player_gamelog(player, season=season, game_type=game_type)
    return list(data.get("gameLog", []))[:limit]


@mcp.tool()
def player_spotlight() -> list[dict]:
    """Players the NHL is currently featuring on the site."""
    return _client.player_spotlight()


@mcp.tool()
def players_digest(players: list[str | int], games: int = 3, boxscore: bool = True) -> str:
    """Pre-formatted text digest for several players at once: current team,
    season totals and the last N games with goals/assists/+-/SOG/faceoff/TOI.
    One call, ready to drop into a report. ``players`` items are names or ids."""
    return format_players_digest(players, games=games, boxscore=boxscore, client=_client)


# --- games -------------------------------------------------------------

@mcp.tool()
def daily_scores(date: str | None = None) -> dict:
    """Scores for a date (YYYY-MM-DD). Omit for today."""
    return _client.daily_scores(date)


@mcp.tool()
def scoreboard(date: str | None = None) -> dict:
    """League scoreboard. Omit ``date`` for the live 'now' scoreboard."""
    return _client.scoreboard(date)


@mcp.tool()
def game_boxscore(game_id: int, player: str | int | None = None) -> dict:
    """Boxscore for a game. With ``player`` (name or id), return just that
    skater's line (SOG, hits, blocks, faceoff%, TOI); otherwise the full box."""
    if player:
        pid = _client.resolve_player(player)
        line = _client.player_boxscore_stats(game_id, pid)
        return {"gameId": game_id, "playerId": pid, "stats": line}
    return _client.game_boxscore(game_id)


@mcp.tool()
def game_play_by_play(game_id: int) -> dict:
    """Full play-by-play event feed for a game."""
    return _client.game_play_by_play(game_id)


@mcp.tool()
def game_landing(game_id: int) -> dict:
    """Gamecenter landing feed: summary, scoring, three stars, matchup."""
    return _client.game_landing(game_id)


@mcp.tool()
def game_story(game_id: int) -> dict:
    """Editorial game story / recap feed."""
    return _client.game_story(game_id)


# --- teams -----------------------------------------------------------

@mcp.tool()
def team_roster(team: str, season: str | int | None = None) -> dict:
    """Roster for a team (3-letter code). Omit ``season`` for the current roster."""
    return _client.team_roster(team, season=season)


@mcp.tool()
def team_prospects(team: str) -> dict:
    """Prospect pool for a team."""
    return _client.team_prospects(team)


@mcp.tool()
def team_schedule(team: str, span: str = "season", when: str | None = None) -> dict:
    """Team schedule. ``span`` = season | month | week. ``when`` = a season id,
    a YYYY-MM month, or a YYYY-MM-DD date; omit for the current period."""
    return _client.team_schedule(team, span=span, when=when)


@mcp.tool()
def team_stats(team: str, season: str | int | None = None, game_type: int = 2) -> dict:
    """Team skater/goalie stat table. Omit ``season`` for the current one."""
    return _client.team_stats(team, season=season, game_type=game_type)


@mcp.tool()
def team_scoreboard(team: str) -> dict:
    """A single team's recent and upcoming games with scores."""
    return _client.team_scoreboard(team)


# --- standings / schedule / leaders ---------------------------------

@mcp.tool()
def standings(date: str | None = None) -> dict:
    """League standings. Omit ``date`` for current; else a YYYY-MM-DD snapshot."""
    return _client.standings(date)


@mcp.tool()
def standings_seasons() -> dict:
    """Per-season standings metadata (format, tiebreakers, date ranges)."""
    return _client.standings_seasons()


@mcp.tool()
def league_schedule(date: str | None = None) -> dict:
    """League-wide schedule for the week containing ``date`` (or now)."""
    return _client.league_schedule(date)


@mcp.tool()
def schedule_calendar(date: str | None = None) -> dict:
    """Month calendar view of the schedule."""
    return _client.schedule_calendar(date)


@mcp.tool()
def skater_leaders(categories: str | None = None, season: str | int | None = None,
                   game_type: int = 2, limit: int = 5) -> dict:
    """Skater stat leaders. ``categories`` e.g. 'goals', 'assists', 'points'.
    Omit ``season`` for current leaders."""
    return _client.skater_leaders(categories=categories, season=season,
                                  game_type=game_type, limit=limit)


@mcp.tool()
def goalie_leaders(categories: str | None = None, season: str | int | None = None,
                   game_type: int = 2, limit: int = 5) -> dict:
    """Goalie stat leaders. ``categories`` e.g. 'wins', 'savePctg', 'gaa'."""
    return _client.goalie_leaders(categories=categories, season=season,
                                  game_type=game_type, limit=limit)


# --- playoffs / draft --------------------------------------------

@mcp.tool()
def playoff_bracket(year: int) -> dict:
    """Playoff bracket for a year (the year the playoffs are played)."""
    return _client.playoff_bracket(year)


@mcp.tool()
def playoff_series_schedule(season: str | int, series_letter: str) -> dict:
    """Game schedule for one playoff series (letter a-o)."""
    return _client.playoff_series_schedule(season, series_letter)


@mcp.tool()
def playoff_carousel(season: str | int) -> dict:
    """Overview of every active playoff series for a season."""
    return _client.playoff_carousel(season)


@mcp.tool()
def draft_rankings(season: str | int | None = None, category: int | None = None) -> dict:
    """Central Scouting draft rankings. ``category``: 1 NA skater, 2 intl skater,
    3 NA goalie, 4 intl goalie. Omit ``season`` for the latest."""
    return _client.draft_rankings(season=season, category=category)


@mcp.tool()
def draft_picks(season: str | int | None = None, round: str = "all") -> dict:
    """Draft picks for a season and round ('all' or 1-7). Omit for the latest."""
    return _client.draft_picks(season=season, round_=round)


@mcp.tool()
def draft_tracker() -> dict:
    """Live draft pick tracker (during the draft)."""
    return _client.draft_tracker()


# --- meta / stats REST / passthrough --------------------------------

@mcp.tool()
def seasons() -> list[int]:
    """Every season id the API knows about (oldest to newest)."""
    return _client.seasons()


@mcp.tool()
def meta(players: str | None = None, teams: str | None = None) -> dict:
    """Metadata bundle. ``players``: comma-separated ids. ``teams``: comma-
    separated 3-letter codes."""
    return _client.meta(players=players, teams=teams)


@mcp.tool()
def stats_report(entity: str = "skater", report: str = "summary",
                 season: str | int | None = None, game_type: int = 2,
                 sort: str | None = None, limit: int = 25,
                 cayenne: str | None = None) -> dict:
    """Aggregate stat table from api.nhle.com/stats/rest. ``entity`` =
    skater | goalie | team. ``report`` e.g. summary, faceoffpercentages,
    realtime, penalties, powerplay, penaltykill, scoringpergame, timeonice.
    ``cayenne`` overrides the default seasonId/gameTypeId filter expression."""
    return _client.stats_report(entity=entity, report=report, season=season,
                                game_type=game_type, sort=sort, limit=limit,
                                cayenne=cayenne)


@mcp.tool()
def nhl_api_get(path: str, params: dict[str, Any] | None = None) -> Any:
    """Escape hatch: GET any endpoint on api-web.nhle.com or
    api.nhle.com/stats/rest that has no dedicated tool (NHL Edge tracking data,
    replays, TV schedule, betting odds, where-to-watch, postal lookup, ...).
    ``path`` may be '/v1/...', 'stats/<lang>/...', or a full URL on those hosts.
    See docs/endpoints.md for the catalog."""
    return _client.passthrough(path, params)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
