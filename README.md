# mcp-nhl

An [MCP](https://modelcontextprotocol.io) server for the **public NHL APIs** —
scores, standings, schedules, rosters, player landing pages, game logs,
boxscores, stat leaders, playoffs and the draft.

- No API key. Every call is a plain HTTP GET.
- Read-only.
- One runtime dependency (`mcp`); the HTTP client is pure standard library.

> **Unofficial.** Not affiliated with, endorsed by, or connected to the National
> Hockey League. Data comes from the NHL's own public endpoints
> (`api-web.nhle.com`, `api.nhle.com/stats/rest`), which may change or disappear
> without notice.

## Install

```bash
pipx install git+https://github.com/StefanOOE/mcp-nhl
# or, from a clone:
python -m venv .venv && .venv/bin/pip install -e .
```

## Run

```bash
mcp-nhl            # console script
python -m mcp_nhl  # equivalent; stdio transport
```

### Claude Desktop / MCP client config

```json
{
  "mcpServers": {
    "nhl": { "command": "mcp-nhl" }
  }
}
```

If you installed into a virtualenv, point `command` at that interpreter and pass
`["-m", "mcp_nhl"]` as `args`.

## Tools

Player arguments accept a **name or a numeric NHL player id**. Season ids are 8
digits (`20252026`). Game type: `2` regular season, `3` playoffs.

| Tool | What it returns |
|---|---|
| `search_players(query, limit, active_only)` | id, name, position, team for name matches |
| `player_summary(player)` | landing page: bio, current team, season + career stats, last 5 games |
| `player_gamelog(player, season?, game_type, limit)` | game-by-game log |
| `player_spotlight()` | players the NHL is currently featuring |
| `players_digest(players, games, boxscore)` | **pre-formatted text** snapshot of several players at once |
| `daily_scores(date?)` / `scoreboard(date?)` | scores for a day / the live scoreboard |
| `game_boxscore(game_id, player?)` | full boxscore, or one skater's line (SOG, hits, blocks, FO%, TOI) |
| `game_play_by_play(game_id)` / `game_landing(game_id)` / `game_story(game_id)` | event feed / gamecenter / recap |
| `team_roster(team, season?)` / `team_prospects(team)` | roster / prospect pool |
| `team_schedule(team, span, when?)` | `span` = season \| month \| week |
| `team_stats(team, season?)` / `team_scoreboard(team)` | team stat table / one team's games |
| `standings(date?)` / `standings_seasons()` | standings now or historical / per-season format |
| `league_schedule(date?)` / `schedule_calendar(date?)` | league schedule week / month calendar |
| `skater_leaders(...)` / `goalie_leaders(...)` | stat leaders (`categories` e.g. `goals`, `wins`) |
| `playoff_bracket(year)` / `playoff_series_schedule(season, letter)` / `playoff_carousel(season)` | playoff views |
| `draft_rankings(...)` / `draft_picks(...)` / `draft_tracker()` | draft data |
| `seasons()` / `meta(players?, teams?)` | season ids / metadata bundle |
| `stats_report(entity, report, season?, sort?, limit, cayenne?)` | any `api.nhle.com/stats/rest` report table |
| `nhl_api_get(path, params?)` | **escape hatch** — GET any other endpoint on the two NHL hosts |

For endpoints without a dedicated tool (NHL Edge tracking data, replays, TV
schedule, betting odds, ...), use `nhl_api_get`. See [`docs/endpoints.md`](docs/endpoints.md).

## Library use

```python
from mcp_nhl import NHLClient, format_players_digest

nhl = NHLClient()
nhl.player_landing("Connor McDavid")
print(format_players_digest(["Marco Rossi", 8483464], games=3))
```

## Development

```bash
pip install -e ".[dev]"
pytest          # offline; uses recorded fixtures in tests/fixtures/
ruff check src tests
```

## Prior art

[`dylangroos/nhl-mcp`](https://github.com/dylangroos/nhl-mcp) is an earlier
TypeScript NHL MCP server focused on teams, standings and stat leaders. `mcp-nhl`
is an independent Python implementation with game logs, boxscores, a multi-player
digest and a generic passthrough.

## License

MIT — see [LICENSE](LICENSE).
