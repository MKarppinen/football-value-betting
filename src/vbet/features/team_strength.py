"""Derive attack and defence strengths from actual FBref xG."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping

from vbet.config import USE_XG


class TeamStrength:
    def __init__(self, matches: Iterable[Mapping[str, object]]) -> None:
        self.matches = list(matches)

        if not self.matches:
            raise ValueError("At least one completed match is required.")

        scored = defaultdict(float)
        conceded = defaultdict(float)
        played = defaultdict(int)

        total_for = 0.0
        observations = 0

        for match in self.matches:
            home = str(match["home_team"])
            away = str(match["away_team"])

            home_value = self._value(match, "home_xg", "home_goals")
            away_value = self._value(match, "away_xg", "away_goals")

            scored[home] += home_value
            conceded[home] += away_value
            scored[away] += away_value
            conceded[away] += home_value

            played[home] += 1
            played[away] += 1

            total_for += home_value + away_value
            observations += 2

        self.league_average = total_for / observations
        self._attack = {}
        self._defence = {}

        for team, count in played.items():
            self._attack[team] = (
                scored[team] / count
            ) / self.league_average

            self._defence[team] = (
                conceded[team] / count
            ) / self.league_average

    @staticmethod
    def _value(
        match: Mapping[str, object],
        xg_key: str,
        goal_key: str,
    ) -> float:
        xg = match.get(xg_key)

        if USE_XG and xg is not None:
            return float(xg)

        return float(match[goal_key])

    def attack(self, team: str) -> float:
        return self._attack[team]

    def defence(self, team: str) -> float:
        return self._defence[team]