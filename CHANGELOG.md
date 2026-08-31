# Changelog

## 0.1.0 (unreleased)

Initial release.

- `NHLClient`: dependency-free client for `api-web.nhle.com`,
  `api.nhle.com/stats/rest` and the player search endpoint.
- MCP server (`python -m mcp_nhl`, stdio) exposing ~30 tools across players,
  games, teams, standings, schedule, stat leaders, playoffs, draft and meta,
  plus `stats_report` for the stats REST report family and `nhl_api_get` as a
  generic passthrough.
- `players_digest`: one-call, pre-formatted multi-player performance snapshot.
