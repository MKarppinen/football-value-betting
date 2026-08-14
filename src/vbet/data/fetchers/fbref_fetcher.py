"""Fetch completed FBref matches and their actual xG values."""
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

        fbref = sd.FBref(
            leagues=self.leagues,
            seasons=self._seasons(),
        )

        schedule = fbref.read_schedule().reset_index()
        schedule.columns = [
            str(column).lower().replace(" ", "_")
            for column in schedule.columns
        ]

        xg_by_match = self._get_xg_by_match(fbref)

        schedule["date"] = pd.to_datetime(
            schedule["date"],
            errors="coerce",
        )

        cutoff = pd.Timestamp.now().normalize() - pd.DateOffset(
            months=self.months
        )

        schedule = schedule[schedule["date"].ge(cutoff)]
        matches: list[dict[str, Any]] = []

        for row in schedule.to_dict("records"):
            home_team = row.get("home_team")
            away_team = row.get("away_team")
            home_goals, away_goals = self._score(row)

            if not home_team or not away_team:
                continue

            if home_goals is None or away_goals is None:
                continue

            match_date = row["date"].date().isoformat()

            xg = xg_by_match.get(
                (match_date, str(home_team), str(away_team)),
                {},
            )

            matches.append(
                {
                    "competition": str(
                        row.get("league") or self.leagues[0]
                    ),
                    "date": match_date,
                    "home_team": str(home_team),
                    "away_team": str(away_team),
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "season": str(row.get("season") or ""),
                    "status": "completed",
                    "source": "fbref",
                    "source_match_id": (
                        str(row.get("game_id") or "") or None
                    ),
                    "stats": {
                        "home_xg": xg.get("home_xg"),
                        "away_xg": xg.get("away_xg"),
                    },
                }
            )

        return matches

    def _get_xg_by_match(self, fbref: Any) -> dict:
        """Build date/home/away -> xG mapping from FBref team match logs."""
        import pandas as pd

        logs = fbref.read_team_match_stats(
            stat_type="schedule"
        ).reset_index()

        logs.columns = [
            str(column).lower().replace(" ", "_")
            for column in logs.columns
        ]

        logs["date"] = pd.to_datetime(
            logs["date"],
            errors="coerce",
        )

        xg_by_match: dict = {}

        for row in logs.to_dict("records"):
            team = row.get("team")
            opponent = row.get("opponent")
            venue = str(row.get("venue") or "").lower()
            xg = self._number(row.get("xg"))

            if not team or not opponent or xg is None:
                continue

            if pd.isna(row["date"]):
                continue

            match_date = row["date"].date().isoformat()

            if venue == "home":
                key = (match_date, str(team), str(opponent))
                xg_by_match.setdefault(key, {})["home_xg"] = xg

            elif venue == "away":
                key = (match_date, str(opponent), str(team))
                xg_by_match.setdefault(key, {})["away_xg"] = xg

        return xg_by_match

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