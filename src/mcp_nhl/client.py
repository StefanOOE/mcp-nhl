"""Thin, dependency-free client for the public NHL APIs.

Two hosts are used:

* ``https://api-web.nhle.com``            -- the modern "web" API (scores,
  schedules, rosters, player landing pages, gamecenter feeds, standings, draft).
* ``https://api.nhle.com/stats/rest/en``  -- the older "stats" REST API
  (aggregate skater / goalie / team report tables).

Plus ``https://search.d3.nhle.com`` for player name search.

No API key is required. Everything is an HTTP GET returning JSON.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

WEB_BASE = "https://api-web.nhle.com"
STATS_BASE = "https://api.nhle.com/stats/rest"
SEARCH_URL = "https://search.d3.nhle.com/api/v1/search/player"

USER_AGENT = "mcp-nhl/0.1 (+https://github.com/StefanOOE/mcp-nhl)"
DEFAULT_TIMEOUT = 15.0

# Hosts the generic passthrough tool is allowed to reach.
_ALLOWED_HOSTS = {"api-web.nhle.com", "api.nhle.com"}


class NHLAPIError(RuntimeError):
    """Raised when an NHL endpoint cannot be reached or returns a non-2xx."""


def _localized(value: Any) -> str:
    """NHL payloads wrap display strings as ``{"default": "..."}``."""
    if isinstance(value, dict):
        return str(value.get("default", ""))
    return "" if value is None else str(value)


class NHLClient:
    """Blocking client. One instance per process is fine; it is stateless
    apart from a cached "current season" id."""

    def __init__(self, *, timeout: float = DEFAULT_TIMEOUT, retries: int = 1,
                 opener: Any | None = None) -> None:
        self.timeout = timeout
        self.retries = max(0, retries)
        self._opener = opener or urllib.request.build_opener()
        self._season_cache: str | None = None

    # ---- transport -----------------------------------------------------

    def _request(self, url: str) -> Any:
        last_err: Exception | None = None
        for attempt in range(self.retries + 1):
            try:
                req = urllib.request.Request(
                    url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
                )
                with self._opener.open(req, timeout=self.timeout) as resp:
                    return json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                last_err = NHLAPIError(f"HTTP {exc.code} for {url}")
                if exc.code in (400, 404):
                    break  # deterministic, no point retrying
            except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
                last_err = NHLAPIError(f"{type(exc).__name__}: {exc} for {url}")
            if attempt < self.retries:
                time.sleep(0.4 * (attempt + 1))
        raise last_err or NHLAPIError(f"request failed: {url}")

    def get(self, path: str, *, base: str = WEB_BASE,
            params: dict[str, Any] | None = None) -> Any:
        """GET ``{base}{path}`` and return decoded JSON."""
        url = base.rstrip("/") + "/" + path.lstrip("/")
        if params:
            clean = {k: v for k, v in params.items() if v is not None}
            if clean:
                url += "?" + urllib.parse.urlencode(clean, safe=" =,")
        return self._request(url)

    # ---- generic passthrough ----------------------------------------------

    def passthrough(self, path: str, params: dict[str, Any] | None = None) -> Any:
        """Reach any endpoint on the two known NHL hosts. GET only.

        ``path`` may be an absolute URL on an allowed host, a ``/v1/...``
        path (web API), or a ``stats/...`` / ``/stats/rest/...`` path
        (stats API).
        """
        p = path.strip()
        if p.startswith("http://") or p.startswith("https://"):
            host = urllib.parse.urlparse(p).hostname or ""
            if host not in _ALLOWED_HOSTS:
                raise NHLAPIError(f"host not allowed: {host!r}")
            return self._request(p + (
                "?" + urllib.parse.urlencode(params, safe=" =,") if params else ""
            ))
        if p.lstrip("/").startswith("stats"):
            sub = p.lstrip("/")
            if sub.startswith("stats/rest/"):
                sub = sub[len("stats/rest/"):]
            elif sub.startswith("stats/"):
                sub = sub[len("stats/"):]
            return self.get(sub, base=STATS_BASE, params=params)
        return self.get(p, base=WEB_BASE, params=params)

    # ---- seasons --------------------------------------------------------

    def seasons(self) -> list[int]:
        return list(self.get("/v1/season"))

    def current_season(self) -> str:
        """Eight-digit season id, e.g. ``"20252026"``."""
        if self._season_cache is None:
            self._season_cache = str(max(self.seasons()))
        return self._season_cache

    # ---- players -------------------------------------------------------

    def search_players(self, query: str, *, limit: int = 10,
                       active_only: bool = False) -> list[dict]:
        url = SEARCH_URL + "?" + urllib.parse.urlencode(
            {"culture": "en-us", "limit": limit, "q": query}
        )
        hits = self._request(url)
        rows = [
            {
                "playerId": int(h["playerId"]),
                "name": h.get("name", ""),
                "position": h.get("positionCode"),
                "team": h.get("teamAbbrev"),
                "active": bool(h.get("active")),
                "lastSeason": h.get("lastSeasonId"),
            }
            for h in hits
            if h.get("playerId")
        ]
        return [r for r in rows if r["active"]] if active_only else rows

    def resolve_player(self, player: str | int) -> int:
        """Accept a numeric id or a name; return a numeric player id."""
        if isinstance(player, int):
            return player
        s = str(player).strip()
        if s.isdigit():
            return int(s)
        hits = self.search_players(s, limit=8)
        exact = [h for h in hits if h["name"].lower() == s.lower()]
        pool = exact or [h for h in hits if h["active"]] or hits
        if not pool:
            raise NHLAPIError(f"no player found for {player!r}")
        return pool[0]["playerId"]

    def player_landing(self, player: str | int) -> dict:
        return self.get(f"/v1/player/{self.resolve_player(player)}/landing")

    def player_gamelog(self, player: str | int, *, season: str | int | None = None,
                       game_type: int = 2) -> dict:
        pid = self.resolve_player(player)
        if season is None:
            return self.get(f"/v1/player/{pid}/game-log/now")
        return self.get(f"/v1/player/{pid}/game-log/{season}/{game_type}")

    def player_spotlight(self) -> list[dict]:
        return list(self.get("/v1/player-spotlight"))

    # ---- games --------------------------------------------------------

    def daily_scores(self, date: str | None = None) -> dict:
        return self.get(f"/v1/score/{date or 'now'}")

    def scoreboard(self, date: str | None = None) -> dict:
        return self.get("/v1/scoreboard/now" if not date else f"/v1/score/{date}")

    def game_boxscore(self, game_id: int) -> dict:
        return self.get(f"/v1/gamecenter/{game_id}/boxscore")

    def game_play_by_play(self, game_id: int) -> dict:
        return self.get(f"/v1/gamecenter/{game_id}/play-by-play")

    def game_landing(self, game_id: int) -> dict:
        return self.get(f"/v1/gamecenter/{game_id}/landing")

    def game_story(self, game_id: int) -> dict:
        return self.get(f"/v1/wsc/game-story/{game_id}")

    def player_boxscore_stats(self, game_id: int, player_id: int) -> dict | None:
        """One skater's box line: SOG, hits, blocks, faceoff%, TOI."""
        box = self.game_boxscore(game_id)
        pbg = box.get("playerByGameStats", {})
        for side in ("awayTeam", "homeTeam"):
            group = pbg.get(side, {})
            for pos in ("forwards", "defense", "goalies"):
                for p in group.get(pos, []):
                    if p.get("playerId") == player_id:
                        fo = p.get("faceoffWinningPctg")
                        return {
                            "sog": p.get("sog"),
                            "hits": p.get("hits"),
                            "blocks": p.get("blockedShots"),
                            "giveaways": p.get("giveaways"),
                            "takeaways": p.get("takeaways"),
                            "faceoffPct": round(fo * 100, 1)
                            if isinstance(fo, (int, float)) else None,
                            "toi": p.get("toi"),
                            "powerPlayToi": p.get("powerPlayToi"),
                            "position": p.get("position"),
                        }
        return None

    # ---- teams -------------------------------------------------------

    def team_roster(self, team: str, *, season: str | int | None = None) -> dict:
        team = team.upper()
        return self.get(f"/v1/roster/{team}/{season or 'current'}")

    def team_prospects(self, team: str) -> dict:
        return self.get(f"/v1/prospects/{team.upper()}")

    def team_schedule(self, team: str, *, span: str = "season",
                      when: str | None = None) -> dict:
        team = team.upper()
        if span == "season":
            return self.get(f"/v1/club-schedule-season/{team}/{when or 'now'}")
        if span == "month":
            return self.get(f"/v1/club-schedule/{team}/month/{when or 'now'}")
        if span == "week":
            return self.get(f"/v1/club-schedule/{team}/week/{when or 'now'}")
        raise NHLAPIError(f"span must be season|month|week, got {span!r}")

    def team_stats(self, team: str, *, season: str | int | None = None,
                   game_type: int = 2) -> dict:
        team = team.upper()
        if season is None:
            return self.get(f"/v1/club-stats/{team}/now")
        return self.get(f"/v1/club-stats/{team}/{season}/{game_type}")

    def team_scoreboard(self, team: str) -> dict:
        return self.get(f"/v1/scoreboard/{team.upper()}/now")

    # ---- standings / schedule / leaders -----------------------------

    def standings(self, date: str | None = None) -> dict:
        return self.get(f"/v1/standings/{date or 'now'}")

    def standings_seasons(self) -> dict:
        return self.get("/v1/standings-season")

    def league_schedule(self, date: str | None = None) -> dict:
        return self.get(f"/v1/schedule/{date or 'now'}")

    def schedule_calendar(self, date: str | None = None) -> dict:
        return self.get(f"/v1/schedule-calendar/{date or 'now'}")

    def skater_leaders(self, *, categories: str | None = None,
                       season: str | int | None = None, game_type: int = 2,
                       limit: int = 5) -> dict:
        params = {"categories": categories, "limit": limit}
        if season is None:
            return self.get("/v1/skater-stats-leaders/current", params=params)
        return self.get(f"/v1/skater-stats-leaders/{season}/{game_type}", params=params)

    def goalie_leaders(self, *, categories: str | None = None,
                       season: str | int | None = None, game_type: int = 2,
                       limit: int = 5) -> dict:
        params = {"categories": categories, "limit": limit}
        if season is None:
            return self.get("/v1/goalie-stats-leaders/current", params=params)
        return self.get(f"/v1/goalie-stats-leaders/{season}/{game_type}", params=params)

    # ---- playoffs / draft ------------------------------------------

    def playoff_bracket(self, year: int) -> dict:
        return self.get(f"/v1/playoff-bracket/{year}")

    def playoff_series_schedule(self, season: str | int, series_letter: str) -> dict:
        return self.get(f"/v1/schedule/playoff-series/{season}/{series_letter.lower()}/")

    def playoff_carousel(self, season: str | int) -> dict:
        return self.get(f"/v1/playoff-series/carousel/{season}/")

    def draft_rankings(self, *, season: str | int | None = None,
                       category: int | None = None) -> dict:
        if season is None:
            return self.get("/v1/draft/rankings/now")
        return self.get(f"/v1/draft/rankings/{season}/{category or 1}")

    def draft_picks(self, *, season: str | int | None = None,
                    round_: str | int = "all") -> dict:
        if season is None:
            return self.get("/v1/draft/picks/now")
        return self.get(f"/v1/draft/picks/{season}/{round_}")

    def draft_tracker(self) -> dict:
        return self.get("/v1/draft-tracker/picks/now")

    # ---- meta / stats REST -------------------------------------------

    def meta(self, *, players: str | None = None, teams: str | None = None) -> dict:
        return self.get("/v1/meta", params={"players": players, "teams": teams})

    def stats_report(self, *, entity: str = "skater", report: str = "summary",
                     season: str | int | None = None, game_type: int = 2,
                     sort: str | None = None, limit: int = 25, start: int = 0,
                     lang: str = "en", cayenne: str | None = None) -> dict:
        if entity not in ("skater", "goalie", "team"):
            raise NHLAPIError("entity must be skater|goalie|team")
        expr = cayenne
        if expr is None:
            season = season or self.current_season()
            expr = f"seasonId={season} and gameTypeId={game_type}"
        params = {
            "isAggregate": "false",
            "isGame": "false",
            "start": start,
            "limit": limit,
            "sort": sort,
            "cayenneExp": expr,
        }
        return self.get(f"{lang}/{entity}/{report}", base=STATS_BASE, params=params)
