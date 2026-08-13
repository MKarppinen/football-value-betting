"""Fetch and normalize historical FBref schedules."""
from __future__ import annotations

from datetime import date
import re
from typing import Any

from vbet.config import LEAGUES, MONTHS_OF_HISTORY


class FBrefFetcher:
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
                "FBref requires pandas and soccerdata."
            ) from error

        frame = (
            sd.FBref(
                leagues=self.leagues,
                seasons=self._seasons(),
            )
            .read_schedule()
            .reset_index()
        )

        frame.columns = [
            str(column).lower().replace(" ", "_")
            for column in frame.columns
        ]
        frame["date"] = pd.to_datetime(frame["date"], errors="coerce")

        cutoff = pd.Timestamp.now().normalize() - pd.DateOffset(
            months=self.months
        )
        frame = frame[frame["date"].ge(cutoff)]

        matches = []

        for row in frame.to_dict("records"):
            home = row.get("home_team")
            away = row.get("away_team")
            home_goals, away_goals = self._score(row)

            if not home or not away:
                continue

            if home_goals is None or away_goals is None:
                continue

            matches.append(
                {
                    "competition": str(
                        row.get("league") or self.leagues[0]
                    ),
                    "date": row["date"].date().isoformat(),
                    "home_team": str(home),
                    "away_team": str(away),
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "season": str(row.get("season") or ""),
                    "status": "completed",
                    "source": "fbref",
                    "source_match_id": (
                        str(row.get("game_id") or "") or None
                    ),
                    "stats": {
                        "home_xg": self._number(row.get("home_xg")),
                        "away_xg": self._number(row.get("away_xg")),
                    },
                }
            )

        return matches

    @staticmethod
    def _score(row: dict[str, Any]) -> tuple[int | None, int | None]:
        home = row.get("home_score")
        away = row.get("away_score")

        if home is not None and away is not None:
            try:
                return int(home), int(away)
            except (TypeError, ValueError):
                pass

        values = re.findall(r"\d+", str(row.get("score") or ""))

        if len(values) >= 2:
            return int(values[0]), int(values[1])

        return None, None

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            if value is None:
                return None
            number = float(value)
            return number if number == number else None
        except (TypeError, ValueError):
            return None