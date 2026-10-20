"""Human-readable multi-player performance digest.

This is the one call that a small model (or a cron job) can make to get a
complete, pre-formatted snapshot of several players at once: current team,
season totals, and the last N games with per-game detail.

With ``since`` it also emits ready-made report bullets for the games after that
date, so the numbers never have to be copied (and mixed up) by the model.
"""

from __future__ import annotations

from .client import NHLAPIError, NHLClient, _localized


def _fmt_plus_minus(value: int) -> str:
    return f"+{value}" if value > 0 else str(value)


def _game_line(game: dict, box: dict | None, position: str) -> str:
    opp = game.get("opponentAbbrev", "?")
    home_away = "H" if game.get("homeRoadFlag") == "H" else "A"
    goals = game.get("goals", 0)
    assists = game.get("assists", 0)
    points = game.get("points", goals + assists)
    plus_minus = _fmt_plus_minus(game.get("plusMinus", 0))

    toi = (box or {}).get("toi") or game.get("toi", "-")
    sog = (box or {}).get("sog")
    if sog is None:
        sog = game.get("shots")
    faceoff = (box or {}).get("faceoffPct")
    faceoff_str = f"{faceoff}%" if (faceoff is not None and position != "D") else "-"

    hits = (box or {}).get("hits")
    blocks = (box or {}).get("blocks")
    extra = ""
    if hits is not None or blocks is not None:
        extra = (f"  hits {hits if hits is not None else '-'}"
                 f" / blocks {blocks if blocks is not None else '-'}")

    return (f"  {game.get('gameDate', '?')}  {home_away} vs {opp:<3}  "
            f"{goals}G {assists}A ({points}P)  {plus_minus}  "
            f"SOG {sog if sog is not None else '-'}  FO {faceoff_str}  "
            f"TOI {toi}{extra}")


def _report_game(game: dict, box: dict | None, position: str) -> str:
    home_away = "H" if game.get("homeRoadFlag") == "H" else "A"
    parts = [f"{game.get('goals', 0)} G", f"{game.get('assists', 0)} A",
             f"+/- {_fmt_plus_minus(game.get('plusMinus', 0))}"]
    sog = (box or {}).get("sog")
    if sog is None:
        sog = game.get("shots")
    if sog is not None:
        parts.append(f"SOG {sog}")
    faceoff = (box or {}).get("faceoffPct")
    if faceoff is not None and position != "D":
        parts.append(f"Faceoff {faceoff}%")
    toi = (box or {}).get("toi") or game.get("toi")
    if toi:
        parts.append(f"TOI {toi}")
    return (f"  * {game.get('gameDate', '?')} ({home_away} vs {game.get('opponentAbbrev', '?')}): "
            + ", ".join(parts))


def _report_block(name: str, team: str, sub: dict, games: list[str]) -> str:
    season = (f"{sub.get('gamesPlayed', 0)} GP, {sub.get('goals', 0)} G, "
              f"{sub.get('assists', 0)} A ({sub.get('points', 0)} Pts), "
              f"+/- {_fmt_plus_minus(sub.get('plusMinus', 0))}") if sub else "no games yet"
    return "\n".join([f"* **{name} ({team}):**", f"  * Season: {season}", *games])


def player_block(client: NHLClient, player: str | int, games: int,
                 boxscore: bool, since: str | None = None) -> tuple[str, str | None]:
    """One player's section of the digest, plus the report bullets for his
    games after ``since`` (None if there are none or ``since`` is not set)."""
    header_id = player if isinstance(player, int) or str(player).isdigit() else "?"
    lines = [f"### {player}  (id {header_id})"]

    try:
        pid = client.resolve_player(player)
    except NHLAPIError as exc:
        lines.append(f"  ERROR resolving player: {exc}")
        return "\n".join(lines), None

    try:
        landing = client.player_landing(pid)
    except NHLAPIError as exc:
        lines.append(f"  ERROR loading profile: {exc}")
        return "\n".join(lines), None

    # Name mismatch guard: if the id points at the wrong person, re-resolve
    # by name via search and note the correction.
    want = str(player).split()[-1].lower() if not str(player).isdigit() else ""
    got = _localized(landing.get("lastName")).lower()
    if want and got and want not in got and got not in want:
        try:
            alt = client.search_players(str(player), limit=8)
            alt = ([h for h in alt if h["name"].lower() == str(player).lower()]
                   or [h for h in alt if h["active"]] or alt)
            if alt and alt[0]["playerId"] != pid:
                pid = alt[0]["playerId"]
                landing = client.player_landing(pid)
                lines[0] = f"### {player}  (id corrected to {pid})"
        except NHLAPIError:
            pass

    full_name = (f"{_localized(landing.get('firstName'))} "
                 f"{_localized(landing.get('lastName'))}").strip() or str(player)
    team = landing.get("currentTeamAbbrev") or "-"
    team_name = _localized(landing.get("fullTeamName"))
    position = landing.get("position", "?")
    number = landing.get("sweaterNumber")
    number_str = f" #{number}" if number else ""
    lines.append(f"  {full_name} - {position}{number_str} - {team}"
                 + (f" ({team_name})" if team_name else ""))

    sub = (((landing.get("featuredStats") or {}).get("regularSeason") or {})
           .get("subSeason") or {})
    if sub:
        season = landing.get("featuredStats", {}).get("season", "?")
        lines.append(
            f"  Season {season}: {sub.get('gamesPlayed', 0)} GP, "
            f"{sub.get('goals', 0)}G {sub.get('assists', 0)}A "
            f"({sub.get('points', 0)}P), +/- {sub.get('plusMinus', 0)}, "
            f"{sub.get('shots', 0)} SOG, {sub.get('pim', 0)} PIM"
        )
    else:
        lines.append("  No season totals yet (no games played).")

    try:
        log = client.player_gamelog(pid)
        game_list = log.get("gameLog") or []
    except NHLAPIError as exc:
        lines.append(f"  ERROR loading game log: {exc}")
        return "\n".join(lines), None

    if not game_list:
        lines.append("  No NHL games this season (minors / loan / injury).")
        return "\n".join(lines), None

    lines.append(f"  Last {min(games, len(game_list))} games:")
    report_games = []
    for game in game_list[:games]:
        box = None
        if boxscore and game.get("gameId"):
            try:
                box = client.player_boxscore_stats(game["gameId"], pid)
            except NHLAPIError:
                box = None
        lines.append(_game_line(game, box, position))
        if since and str(game.get("gameDate", "")) > since:
            report_games.append(_report_game(game, box, position))
    report = _report_block(full_name, team, sub, report_games) if report_games else None
    return "\n".join(lines), report


def format_players_digest(players: list[str | int], games: int = 3,
                          boxscore: bool = True, since: str | None = None, *,
                          client: NHLClient | None = None) -> str:
    """Formatted digest for several players. ``players`` items may be names
    or numeric ids. ``since`` (YYYY-MM-DD) adds a REPORT LINES section with
    ready-made bullets for every game after that date."""
    client = client or NHLClient()
    games = max(1, min(int(games), 20))
    results = [player_block(client, p, games, boxscore, since) for p in players]
    out = "# NHL player digest\n" + f"# {len(players)} players, last {games} games\n\n" + \
        "\n\n".join(text for text, _ in results)
    if not since:
        return out
    reports = [report for _, report in results if report]
    quiet = [text.splitlines()[1].split(" - ")[0].strip() if len(text.splitlines()) > 1
             else text.splitlines()[0] for text, report in results if not report]
    section = [f"\n\n## REPORT LINES (NHL games after {since}) - copy verbatim, do not change"]
    section += reports or ["(no NHL games after this date)"]
    if quiet and reports:
        section.append(f"No NHL game after {since}: {', '.join(quiet)}")
    return out + "\n\n".join(section)
