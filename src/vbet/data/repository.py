"""Database persistence and read queries."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from vbet.data.database import Database


STAT_COLUMNS = frozenset(
    {
        "home_xg",
        "away_xg",
        "home_shots",
        "away_shots",
        "home_shots_on_target",
        "away_shots_on_target",
        "home_possession",
        "away_possession",
        "home_passes",
        "away_passes",
        "home_pass_accuracy",
        "away_pass_accuracy",
        "home_yellow",
        "away_yellow",
        "home_red",
        "away_red",
        "home_corners",
        "away_corners",
    }
)


class MatchRepository:
    def __init__(
        self,
        database: Database | None = None,
    ) -> None:
        self.database = database or Database()
        self.database.initialize()

    # =========================================================
    # ID HELPERS
    # =========================================================

    @staticmethod
    def _id(
        connection: Any,
        table: str,
        name: str,
        competition_id: int | None = None,
        country: str | None = None,
    ) -> int:

        if table == "competitions":

            connection.execute(
                """
                INSERT OR IGNORE INTO competitions(
                    name,
                    country
                )
                VALUES (?, ?)
                """,
                (
                    name,
                    country,
                ),
            )

            return connection.execute(
                """
                SELECT id
                FROM competitions
                WHERE name = ?
                  AND country IS ?
                """,
                (
                    name,
                    country,
                ),
            ).fetchone()[0]

        connection.execute(
            """
            INSERT OR IGNORE INTO teams(
                name,
                competition_id
            )
            VALUES (?, ?)
            """,
            (
                name,
                competition_id,
            ),
        )

        return connection.execute(
            """
            SELECT id
            FROM teams
            WHERE name = ?
              AND competition_id = ?
            """,
            (
                name,
                competition_id,
            ),
        ).fetchone()[0]

    # =========================================================
    # SAVE HISTORICAL MATCH
    # =========================================================

    def save_match(
        self,
        match: Mapping[str, Any],
    ) -> int:

        with self.database.connect() as c:

            competition_id = self._id(
                c,
                "competitions",
                str(match["competition"]),
                country=match.get("country"),
            )

            home_id = self._id(
                c,
                "teams",
                str(match["home_team"]),
                competition_id,
            )

            away_id = self._id(
                c,
                "teams",
                str(match["away_team"]),
                competition_id,
            )

            c.execute(
                """
                INSERT INTO matches(
                    competition_id,
                    match_date,
                    home_team_id,
                    away_team_id,
                    home_goals,
                    away_goals,
                    season,
                    status,
                    source,
                    source_match_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

                ON CONFLICT(
                    competition_id,
                    match_date,
                    home_team_id,
                    away_team_id
                )
                DO UPDATE SET
                    home_goals = excluded.home_goals,
                    away_goals = excluded.away_goals,
                    status = excluded.status,
                    season = excluded.season,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    competition_id,
                    match["date"],
                    home_id,
                    away_id,
                    match.get("home_goals"),
                    match.get("away_goals"),
                    match.get("season"),
                    match.get("status", "completed"),
                    match.get("source", "manual"),
                    match.get("source_match_id"),
                ),
            )

            match_id = c.execute(
                """
                SELECT id
                FROM matches
                WHERE competition_id = ?
                  AND match_date = ?
                  AND home_team_id = ?
                  AND away_team_id = ?
                """,
                (
                    competition_id,
                    match["date"],
                    home_id,
                    away_id,
                ),
            ).fetchone()[0]

            stats = {
                key: value
                for key, value in match.get("stats", {}).items()
                if key in STAT_COLUMNS
            }

            if stats:

                fields = ", ".join(stats)

                placeholders = ", ".join(
                    "?"
                    for _ in stats
                )

                update = ", ".join(
                    f"{key}=excluded.{key}"
                    for key in stats
                )

                c.execute(
                    f"""
                    INSERT INTO match_stats(
                        match_id,
                        {fields}
                    )
                    VALUES (?, {placeholders})

                    ON CONFLICT(match_id)
                    DO UPDATE SET {update}
                    """,
                    [
                        match_id,
                        *stats.values(),
                    ],
                )

            return int(match_id)

    # =========================================================
    # SAVE MULTIPLE MATCHES
    # =========================================================

    def save_matches(
        self,
        matches: Iterable[Mapping[str, Any]],
    ) -> int:

        return sum(
            1
            for match in matches
            if self.save_match(match)
        )

    # =========================================================
    # SAVE SCHEDULED MATCH
    # =========================================================

    def save_scheduled_match(
        self,
        match: Mapping[str, Any],
    ) -> int:
        """Save or find a scheduled match from an external source."""

        with self.database.connect() as c:

            competition_id = self._id(
                c,
                "competitions",
                str(match["competition"]),
                country=match.get("country"),
            )

            home_id = self._id(
                c,
                "teams",
                str(match["home_team"]),
                competition_id,
            )

            away_id = self._id(
                c,
                "teams",
                str(match["away_team"]),
                competition_id,
            )

            c.execute(
                """
                INSERT OR IGNORE INTO matches(
                    competition_id,
                    match_date,
                    home_team_id,
                    away_team_id,
                    season,
                    status,
                    source,
                    source_match_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    competition_id,
                    match["date"],
                    home_id,
                    away_id,
                    match.get("season"),
                    match.get("status", "scheduled"),
                    match.get("source", "odds_api"),
                    match.get("source_match_id"),
                ),
            )

            row = c.execute(
                """
                SELECT id
                FROM matches
                WHERE competition_id = ?
                  AND match_date = ?
                  AND home_team_id = ?
                  AND away_team_id = ?
                """,
                (
                    competition_id,
                    match["date"],
                    home_id,
                    away_id,
                ),
            ).fetchone()

            if row is None:
                raise RuntimeError(
                    "Ottelua ei voitu löytää tallennuksen jälkeen."
                )

            return int(row["id"])

    # =========================================================
    # SAVE BOOKMAKER ODDS
    # =========================================================

    def save_odds(
        self,
        match_id: int,
        bookmakers: Iterable[Mapping[str, Any]],
    ) -> int:
        """Save bookmaker 1X2 odds for a match."""

        saved = 0

        with self.database.connect() as c:

            for bookmaker in bookmakers:

                home_odds = bookmaker.get("home_odds")
                draw_odds = bookmaker.get("draw_odds")
                away_odds = bookmaker.get("away_odds")

                if (
                    home_odds is None
                    or draw_odds is None
                    or away_odds is None
                ):
                    continue

                c.execute(
                    """
                    INSERT INTO odds(
                        match_id,
                        bookmaker,
                        market,
                        home_odds,
                        draw_odds,
                        away_odds
                    )
                    VALUES (?, ?, '1x2', ?, ?, ?)
                    """,
                    (
                        match_id,
                        bookmaker["title"],
                        home_odds,
                        draw_odds,
                        away_odds,
                    ),
                )

                saved += 1

        return saved

    # =========================================================
    # FIND MATCH
    # =========================================================

    def find_match(
        self,
        home_team: str,
        away_team: str,
        match_date: str,
        competition: str = "Premier League",
    ) -> int | None:
        """Find a match by teams and date."""

        with self.database.connect() as c:

            row = c.execute(
                """
                SELECT m.id
                FROM matches m

                JOIN teams h
                    ON h.id = m.home_team_id

                JOIN teams a
                    ON a.id = m.away_team_id

                JOIN competitions comp
                    ON comp.id = m.competition_id

                WHERE h.name = ?
                  AND a.name = ?
                  AND DATE(m.match_date) = DATE(?)
                  AND comp.name = ?

                LIMIT 1
                """,
                (
                    home_team,
                    away_team,
                    match_date,
                    competition,
                ),
            ).fetchone()

            return int(row["id"]) if row else None

    # =========================================================
    # COMPLETED MATCHES
    # =========================================================

    def completed_matches(
        self,
        competition: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return completed matches with their xG data."""

        sql = """
            SELECT
                m.match_date,
                h.name AS home_team,
                a.name AS away_team,
                m.home_goals,
                m.away_goals,
                s.home_xg,
                s.away_xg

            FROM matches m

            JOIN teams h
                ON h.id = m.home_team_id

            JOIN teams a
                ON a.id = m.away_team_id

            JOIN competitions c
                ON c.id = m.competition_id

            LEFT JOIN match_stats s
                ON s.match_id = m.id

            WHERE m.home_goals IS NOT NULL
              AND m.away_goals IS NOT NULL
        """

        args: list[str] = []

        if competition:

            sql += """
                AND c.name = ?
            """

            args.append(competition)

        sql += """
            ORDER BY m.match_date ASC
        """

        with self.database.connect() as c:

            return [
                dict(row)
                for row in c.execute(
                    sql,
                    args,
                ).fetchall()
            ]

    # =========================================================
    # UPCOMING MATCHES WITHOUT ODDS
    # =========================================================

    def upcoming_matches_without_odds(
        self,
        competition: str = "Premier League",
    ) -> list[dict[str, Any]]:
        """
        Return upcoming scheduled matches.

        This method does NOT read the odds table.

        It is used when we only want to calculate:
            1 probability
            X probability
            2 probability
            fair odds
        """

        with self.database.connect() as c:

            rows = c.execute(
                """
                SELECT
                    m.id AS match_id,
                    m.match_date,
                    h.name AS home_team,
                    a.name AS away_team,
                    comp.name AS competition

                FROM matches m

                JOIN teams h
                    ON h.id = m.home_team_id

                JOIN teams a
                    ON a.id = m.away_team_id

                JOIN competitions comp
                    ON comp.id = m.competition_id

                WHERE m.status = 'scheduled'
                  AND datetime(m.match_date) >= datetime('now')
                  AND comp.name = ?

                ORDER BY
                    datetime(m.match_date) ASC
                """,
                (
                    competition,
                ),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # =========================================================
    # THIS WEEK'S MATCHES
    # =========================================================

    def matches_this_week(
        self,
        competition: str = "Premier League",
    ) -> list[dict[str, Any]]:
        """
        Return scheduled matches from the current calendar week.

        Monday is treated as the first day of the week.
        """

        with self.database.connect() as c:

            rows = c.execute(
                """
                SELECT
                    m.id AS match_id,
                    m.match_date,
                    h.name AS home_team,
                    a.name AS away_team,
                    comp.name AS competition

                FROM matches m

                JOIN teams h
                    ON h.id = m.home_team_id

                JOIN teams a
                    ON a.id = m.away_team_id

                JOIN competitions comp
                    ON comp.id = m.competition_id

                WHERE m.status = 'scheduled'
                  AND comp.name = ?

                  AND DATE(m.match_date)
                      >= DATE('now', 'weekday 1', '-7 days')

                  AND DATE(m.match_date)
                      < DATE('now', 'weekday 1', '+7 days')

                ORDER BY
                    datetime(m.match_date) ASC
                """,
                (
                    competition,
                ),
            ).fetchall()

        return [
            dict(row)
            for row in rows
        ]

    # =========================================================
    # UPCOMING MATCHES WITH ODDS
    # =========================================================

    def upcoming_matches(self) -> list[dict[str, Any]]:
        """
        Return upcoming matches with their latest bookmaker odds.

        This method is kept for the value-bet scanner.
        """

        with self.database.connect() as c:

            rows = c.execute(
                """
                SELECT
                    m.id AS match_id,
                    m.match_date,
                    h.name AS home_team,
                    a.name AS away_team,

                    o.bookmaker,
                    o.home_odds,
                    o.draw_odds,
                    o.away_odds,
                    o.fetched_at

                FROM matches m

                JOIN teams h
                    ON h.id = m.home_team_id

                JOIN teams a
                    ON a.id = m.away_team_id

                JOIN odds o
                    ON o.match_id = m.id

                WHERE m.status = 'scheduled'
                  AND datetime(m.match_date) >= datetime('now')

                  AND o.id = (
                      SELECT o2.id

                      FROM odds o2

                      WHERE o2.match_id = o.match_id
                        AND o2.bookmaker = o.bookmaker

                      ORDER BY
                          o2.fetched_at DESC,
                          o2.id DESC

                      LIMIT 1
                  )

                ORDER BY
                    datetime(m.match_date) ASC
                """
            ).fetchall()

        matches: dict[int, dict[str, Any]] = {}

        for row in rows:

            match_id = int(
                row["match_id"]
            )

            if match_id not in matches:

                matches[match_id] = {
                    "match_id": match_id,
                    "match_date": row["match_date"],
                    "home_team": row["home_team"],
                    "away_team": row["away_team"],
                    "bookmakers": [],
                }

            matches[match_id]["bookmakers"].append(
                {
                    "bookmaker": row["bookmaker"],
                    "home_odds": row["home_odds"],
                    "draw_odds": row["draw_odds"],
                    "away_odds": row["away_odds"],
                    "fetched_at": row["fetched_at"],
                }
            )

        return list(
            matches.values()
        )