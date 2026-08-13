"""Poisson-based 1X2 football match probabilities."""
from __future__ import annotations

import math


class PoissonModel:
    def __init__(self, league_average: float, home_advantage: float = 1.10, max_goals: int = 10) -> None:
        self.league_average, self.home_advantage, self.max_goals = league_average, home_advantage, max_goals

    @staticmethod
    def _pmf(goals: int, rate: float) -> float:
        return math.exp(-rate) * rate**goals / math.factorial(goals)

    def predict(self, home_attack: float, home_defence: float, away_attack: float, away_defence: float) -> dict[str, float]:
        home_rate = self.league_average * home_attack * away_defence * self.home_advantage
        away_rate = self.league_average * away_attack * home_defence
        home = draw = away = 0.0
        for hg in range(self.max_goals + 1):
            for ag in range(self.max_goals + 1):
                probability = self._pmf(hg, home_rate) * self._pmf(ag, away_rate)
                if hg > ag: home += probability
                elif hg == ag: draw += probability
                else: away += probability
        total = home + draw + away
        return {"home": home / total, "draw": draw / total, "away": away / total, "home_goals": home_rate, "away_goals": away_rate}
