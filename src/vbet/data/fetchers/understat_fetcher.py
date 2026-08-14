"""Fetch historical match results and xG data from Understat."""
from __future__ import annotations

from datetime import date
from typing import Any

from vbet.config import LEAGUES, MONTHS_OF_HISTORY


class UnderstatFetcher:
    def __init__(
        self,
        leagues: list[str] | None = None,
        months: int | None = None,
    ) -> None:
        self.leagues = leagues or LEAGUES
        self.months = months or MONTHS_OF_HISTORY

    def _seasons(self) -> list[int]:
        today = date.today()
        current = today.year if today.month >= 7 else today.year - 1

        return list(range(current - (self.months // 12 + 1), current + 1))

    def get_matches(self) -> list[dict[str, Any]]:
        try:
            import pandas as pd
            import soccerdata as sd
        except ImportError as error:
            raise RuntimeError(
                "Understat-haku vaatii pandas- ja soccerdata-paketit."
            ) from error

        understat = sd.Understat(
            leagues=self.leagues,
            seasons=self._seasons(),
        )

        frame = understat.read_team_match_stats().reset_index()

        frame.columns = [
            str(column).lower().replace(" ", "_")
            for column in frame.columns
        ]

        frame["date"] = pd.to_datetime(
            frame["date"],
            errors="coerce",
        )

        cutoff = pd.Timestamp.now().normalize() - pd.DateOffset(
            months=self.months
        )

        frame = frame[frame["date"].ge(cutoff)]
        matches: list[dict[str, Any]] = []

        for row in frame.to_dict("records"):
            home_team = row.get("home_team")
            away_team = row.get("away_team")

            home_goals = self._integer(row.get("home_goals"))
            away_goals = self._integer(row.get("away_goals"))

            home_xg = self._number(row.get("home_xg"))
            away_xg = self._number(row.get("away_xg"))

            if not home_team or not away_team:
                continue

            if home_goals is None or away_goals is None:
                continue

            if home_xg is None or away_xg is None:
                continue

            matches.append(
                {
                    "competition": str(
                        row.get("league") or self.leagues[0]
                    ),
                    "date": row["date"].date().isoformat(),
                    "home_team": str(home_team),
                    "away_team": str(away_team),
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "season": str(row.get("season") or ""),
                    "status": "completed",
                    "source": "understat",
                    "source_match_id": (
                        str(
                            row.get("game_id")
                            or row.get("game")
                            or ""
                        )
                        or None
                    ),
                    "stats": {
                        "home_xg": home_xg,
                        "away_xg": away_xg,
                    },
                }
            )

        return matches

    @staticmethod
    def _integer(value: Any) -> int | None:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            if value is None:
                return None

            number = float(value)
            return number if number == number else None
        except (TypeError, ValueError):
            return None