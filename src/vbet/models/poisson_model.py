"""Poisson model for football match probabilities."""

from __future__ import annotations

import math

from vbet.features.team_strength import TeamStrength


class PoissonModel:
    def __init__(self, team_strength: TeamStrength) -> None:
        self.team_strength = team_strength

    def expected_goals(
        self,
        home_team: str,
        away_team: str,
    ) -> tuple[float, float]:
        """
        Calculate expected goals for both teams.

        Home expected xG:
            (home team's home scored xG
             + away team's away conceded xG) / 2

        Away expected xG:
            (away team's away scored xG
             + home team's home conceded xG) / 2
        """

        home_scored = self.team_strength.home_scored_xg(home_team)
        home_conceded = self.team_strength.home_conceded_xg(home_team)

        away_scored = self.team_strength.away_scored_xg(away_team)
        away_conceded = self.team_strength.away_conceded_xg(away_team)

        home_xg = (home_scored + away_conceded) / 2
        away_xg = (away_scored + home_conceded) / 2

        return home_xg, away_xg

    @staticmethod
    def poisson_probability(
        goals: int,
        expected_goals: float,
    ) -> float:
        """
        Probability of scoring exactly `goals` goals
        with Poisson distribution.
        """

        if goals < 0:
            return 0.0

        return (
            math.exp(-expected_goals)
            * expected_goals**goals
            / math.factorial(goals)
        )

    def score_probability(
        self,
        home_goals: int,
        away_goals: int,
        home_xg: float,
        away_xg: float,
    ) -> float:
        """
        Probability of an exact scoreline.
        """

        home_probability = self.poisson_probability(
            home_goals,
            home_xg,
        )

        away_probability = self.poisson_probability(
            away_goals,
            away_xg,
        )

        return home_probability * away_probability

    def match_probabilities(
        self,
        home_team: str,
        away_team: str,
        max_goals: int = 10,
    ) -> dict[str, float]:
        """
        Calculate 1/X/2 probabilities.

        max_goals controls how many goals are included
        in the Poisson score matrix.
        """

        home_xg, away_xg = self.expected_goals(
            home_team,
            away_team,
        )

        home_win = 0.0
        draw = 0.0
        away_win = 0.0

        for home_goals in range(max_goals + 1):
            for away_goals in range(max_goals + 1):

                probability = self.score_probability(
                    home_goals,
                    away_goals,
                    home_xg,
                    away_xg,
                )

                if home_goals > away_goals:
                    home_win += probability

                elif home_goals == away_goals:
                    draw += probability

                else:
                    away_win += probability

        return {
            "home_win": home_win,
            "draw": draw,
            "away_win": away_win,
        }

    def predict(
        self,
        home_team: str,
        away_team: str,
    ) -> dict[str, float]:
        """
        Return expected goals and 1/X/2 probabilities.
        """

        home_xg, away_xg = self.expected_goals(
            home_team,
            away_team,
        )

        probabilities = self.match_probabilities(
            home_team,
            away_team,
        )

        return {
            "home_xg": home_xg,
            "away_xg": away_xg,
            **probabilities,
        }