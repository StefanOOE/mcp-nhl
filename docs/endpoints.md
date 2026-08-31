# NHL API endpoint catalog

Everything below is reachable through the `nhl_api_get` tool (GET only, hosts
`api-web.nhle.com` and `api.nhle.com` only). Endpoints with a dedicated tool are
marked. Paths are relative to `https://api-web.nhle.com` unless noted.

Endpoint list compiled from
[`Zmalski/NHL-API-Reference`](https://github.com/Zmalski/NHL-API-Reference) (MIT).
The NHL publishes no official documentation; treat everything as best-effort.

## Players

| Path | Dedicated tool |
|---|---|
| `/v1/player/{id}/landing` | `player_summary` |
| `/v1/player/{id}/game-log/now` | `player_gamelog` |
| `/v1/player/{id}/game-log/{season}/{game-type}` | `player_gamelog` |
| `/v1/player-spotlight` | `player_spotlight` |
| `https://search.d3.nhle.com/api/v1/search/player?culture=en-us&q=...` | `search_players` |
| `/v1/skater-stats-leaders/current` · `/{season}/{game-type}` | `skater_leaders` |
| `/v1/goalie-stats-leaders/current` · `/{season}/{game-type}` | `goalie_leaders` |

## Games

| Path | Dedicated tool |
|---|---|
| `/v1/score/now` · `/v1/score/{date}` | `daily_scores` |
| `/v1/scoreboard/now` | `scoreboard` |
| `/v1/gamecenter/{game-id}/boxscore` | `game_boxscore` |
| `/v1/gamecenter/{game-id}/play-by-play` | `game_play_by_play` |
| `/v1/gamecenter/{game-id}/landing` | `game_landing` |
| `/v1/gamecenter/{game-id}/right-rail` | — |
| `/v1/wsc/game-story/{game-id}` | `game_story` |
| `/v1/wsc/play-by-play/{game-id}` | — |
| `/v1/ppt-replay/{game-id}/{event-number}` · `/ppt-replay/goal/...` | — |
| `/v1/where-to-watch` | — |
| `/v1/network/tv-schedule/now` · `/{date}` | — |
| `/v1/partner-game/{country}/now` (odds) | — |

## Teams

| Path | Dedicated tool |
|---|---|
| `/v1/roster/{team}/current` · `/{season}` | `team_roster` |
| `/v1/roster-season/{team}` | — |
| `/v1/prospects/{team}` | `team_prospects` |
| `/v1/club-schedule-season/{team}/now` · `/{season}` | `team_schedule` (season) |
| `/v1/club-schedule/{team}/month/{now\|YYYY-MM}` | `team_schedule` (month) |
| `/v1/club-schedule/{team}/week/{now\|date}` | `team_schedule` (week) |
| `/v1/club-stats/{team}/now` · `/{season}/{game-type}` | `team_stats` |
| `/v1/club-stats-season/{team}` | — |
| `/v1/scoreboard/{team}/now` | `team_scoreboard` |

## Standings / schedule

| Path | Dedicated tool |
|---|---|
| `/v1/standings/now` · `/v1/standings/{date}` | `standings` |
| `/v1/standings-season` | `standings_seasons` |
| `/v1/schedule/now` · `/v1/schedule/{date}` | `league_schedule` |
| `/v1/schedule-calendar/now` · `/{date}` | `schedule_calendar` |

## Playoffs / draft / season

| Path | Dedicated tool |
|---|---|
| `/v1/playoff-bracket/{year}` | `playoff_bracket` |
| `/v1/schedule/playoff-series/{season}/{letter}/` | `playoff_series_schedule` |
| `/v1/playoff-series/carousel/{season}/` | `playoff_carousel` |
| `/v1/draft/rankings/now` · `/{season}/{category}` | `draft_rankings` |
| `/v1/draft/picks/now` · `/{season}/{round}` | `draft_picks` |
| `/v1/draft-tracker/picks/now` | `draft_tracker` |
| `/v1/season` | `seasons` |
| `/v1/meta`, `/v1/meta/game/{id}`, `/v1/location`, `/v1/postal-lookup/{code}` | `meta` (first only) |

## NHL Edge (advanced tracking)

No dedicated tools — all via `nhl_api_get`:

- `/v1/edge/skater-detail/{player-id}/{season}/{game-type}` · `/now`
- `/v1/edge/skater-landing/{season}/{game-type}` · `/now`
- `/v1/edge/team-detail/{team-id}/{season}/{game-type}` · `/now`
- `/v1/edge/team-comparison/{team-id}/{season}/{game-type}`
- `/v1/edge/team-skating-speed-detail/...`, `team-skating-distance-detail/...`,
  `team-zone-time-details/...`, `team-shot-speed-detail/...`,
  `team-shot-location-detail/...` and their `-top-10` variants

## Stats REST (`api.nhle.com/stats/rest/en`)

Use `stats_report(entity=..., report=..., ...)`, or `nhl_api_get("stats/en/...")`.

- `skater/summary`, `goalie/summary`, `team/summary`
- `skater/{report}` where report ∈ `bios`, `faceoffpercentages`,
  `faceoffwins`, `goalsForAgainst`, `realtime`, `penalties`, `penaltykill`,
  `powerplay`, `puckPossessions`, `summaryshooting`, `percentages`,
  `scoringRates`, `scoringpergame`, `shootout`, `timeonice`, `toi`
- `goalie/{report}` ∈ `advanced`, `bios`, `daysrest`, `penaltyShots`,
  `savesByStrength`, `shootout`, `startedVsRelieved`
- `team/{report}` ∈ `daysbetweengames`, `faceoffpercentages`,
  `goalsagainstbystrength`, `goalsbyperiod`, `realtime`, `penalties`,
  `penaltykill`, `powerplay`, `shotsagainstbyperiod`, `summaryshooting`
- Filtering via `cayenneExp`, e.g. `seasonId=20242025 and gameTypeId=2`
