"""Database persistence and read queries."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from vbet.data.database import Database

STAT_COLUMNS = frozenset({"home_xg", "away_xg", "home_shots", "away_shots", "home_shots_on_target", "away_shots_on_target", "home_possession", "away_possession", "home_passes", "away_passes", "home_pass_accuracy", "away_pass_accuracy", "home_yellow", "away_yellow", "home_red", "away_red", "home_corners", "away_corners"})


class MatchRepository:
    def __init__(self, database: Database | None = None) -> None:
        self.database = database or Database()
        self.database.initialize()

    @staticmethod
    def _id(connection: Any, table: str, name: str, competition_id: int | None = None, country: str | None = None) -> int:
        if table == "competitions":
            connection.execute("INSERT OR IGNORE INTO competitions(name, country) VALUES (?, ?)", (name, country))
            return connection.execute("SELECT id FROM competitions WHERE name=? AND country IS ?", (name, country)).fetchone()[0]
        connection.execute("INSERT OR IGNORE INTO teams(name, competition_id) VALUES (?, ?)", (name, competition_id))
        return connection.execute("SELECT id FROM teams WHERE name=? AND competition_id=?", (name, competition_id)).fetchone()[0]

    def save_match(self, match: Mapping[str, Any]) -> int:
        with self.database.connect() as c:
            competition_id = self._id(c, "competitions", str(match["competition"]), country=match.get("country"))
            home_id = self._id(c, "teams", str(match["home_team"]), competition_id)
            away_id = self._id(c, "teams", str(match["away_team"]), competition_id)
            c.execute("""INSERT INTO matches(competition_id,match_date,home_team_id,away_team_id,home_goals,away_goals,season,status,source,source_match_id)
                VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(competition_id,match_date,home_team_id,away_team_id) DO UPDATE SET
                home_goals=excluded.home_goals,away_goals=excluded.away_goals,status=excluded.status,season=excluded.season,updated_at=CURRENT_TIMESTAMP""",
                (competition_id,match["date"],home_id,away_id,match.get("home_goals"),match.get("away_goals"),match.get("season"),match.get("status","completed"),match.get("source","manual"),match.get("source_match_id")))
            match_id = c.execute("SELECT id FROM matches WHERE competition_id=? AND match_date=? AND home_team_id=? AND away_team_id=?",(competition_id,match["date"],home_id,away_id)).fetchone()[0]
            stats = {k:v for k,v in match.get("stats", {}).items() if k in STAT_COLUMNS}
            if stats:
                fields = ", ".join(stats); placeholders = ", ".join("?" for _ in stats)
                update = ", ".join(f"{k}=excluded.{k}" for k in stats)
                c.execute(f"INSERT INTO match_stats(match_id,{fields}) VALUES(?,{placeholders}) ON CONFLICT(match_id) DO UPDATE SET {update}",[match_id,*stats.values()])
            return int(match_id)

    def save_matches(self, matches: Iterable[Mapping[str, Any]]) -> int:
        return sum(1 for match in matches if self.save_match(match))

    def completed_matches(self, competition: str | None = None) -> list[dict[str, Any]]:
        sql = """SELECT m.match_date, h.name home_team, a.name away_team, m.home_goals, m.away_goals, s.home_xg, s.away_xg
                 FROM matches m JOIN teams h ON h.id=m.home_team_id JOIN teams a ON a.id=m.away_team_id
                 JOIN competitions c ON c.id=m.competition_id LEFT JOIN match_stats s ON s.match_id=m.id
                 WHERE m.home_goals IS NOT NULL AND m.away_goals IS NOT NULL"""
        args: list[str] = []
        if competition: sql += " AND c.name=?"; args.append(competition)
        with self.database.connect() as c:
            return [dict(row) for row in c.execute(sql, args).fetchall()]
