"""Dixon-Coles football model using weighted xG."""

from __future__ import annotations

import math

from vbet.features.team_strength import TeamStrength


class PoissonModel:
    """
    Dixon-Coles model built on the 60/40 weighted xG model.

    Home team:
        60% home-specific performance
        40% away-specific performance

    Away team:
        60% away-specific performance
        40% home-specific performance

    Home expected goals are multiplied by a configurable
    home-advantage factor.

    Dixon-Coles corrects the low-scoring outcomes:
        0-0
        1-0
        0-1
        1-1
    """

    HOME_AWAY_WEIGHT = 0.60
    OVERALL_WEIGHT = 0.40

    # Default Dixon-Coles parameter.
    RHO = -0.25

    # Default home advantage.
    HOME_ADVANTAGE = 1.14

    def __init__(
        self,
        team_strength: TeamStrength,
        home_advantage: float | None = None,
        dixon_coles_rho: float | None = None,
    ) -> None:
        self.team_strength = team_strength

        if home_advantage is None:
            self.home_advantage = self.HOME_ADVANTAGE
        else:
            if home_advantage <= 0:
                raise ValueError(
                    "home_advantage must be greater than 0."
                )

            self.home_advantage = home_advantage

        if dixon_coles_rho is None:
            self.dixon_coles_rho = self.RHO
        else:
            self.dixon_coles_rho = dixon_coles_rho

    # =============================================================
    # EXPECTED GOALS
    # =============================================================

    def expected_goals(
        self,
        home_team: str,
        away_team: str,
    ) -> tuple[float, float]:
        """
        Calculate expected goals.

        Home attack:
            60% home attack
            40% away attack

        Home defence:
            60% home defence
            40% away defence

        Away attack:
            60% away attack
            40% home attack

        Away defence:
            60% away defence
            40% home defence

        Home advantage is applied after calculating
        the base home expected goals.
        """

        # -------------------------------------------------
        # HOME ATTACK
        # -------------------------------------------------

        home_attack = (
            self.team_strength.weighted_home_attack(
                home_team
            )
        )

        # -------------------------------------------------
        # HOME DEFENCE
        # -------------------------------------------------

        home_defence = (
            self.team_strength.weighted_home_defence(
                home_team
            )
        )

        # -------------------------------------------------
        # AWAY ATTACK
        # -------------------------------------------------

        away_attack = (
            self.team_strength.weighted_away_attack(
                away_team
            )
        )

        # -------------------------------------------------
        # AWAY DEFENCE
        # -------------------------------------------------

        away_defence = (
            self.team_strength.weighted_away_defence(
                away_team
            )
        )

        # -------------------------------------------------
        # BASE EXPECTED GOALS
        # -------------------------------------------------

        home_xg = (
            home_attack + away_defence
        ) / 2

        away_xg = (
            away_attack + home_defence
        ) / 2

        # -------------------------------------------------
        # HOME ADVANTAGE
        # -------------------------------------------------

        home_xg *= self.home_advantage

        return home_xg, away_xg

    # =============================================================
    # POISSON
    # =============================================================

    @staticmethod
    def poisson_probability(
        goals: int,
        expected_goals: float,
    ) -> float:
        """Probability of exactly `goals` goals."""

        if goals < 0:
            return 0.0

        if expected_goals < 0:
            return 0.0

        return (
            math.exp(-expected_goals)
            * expected_goals**goals
            / math.factorial(goals)
        )

    # =============================================================
    # DIXON-COLES CORRECTION
    # =============================================================

    @staticmethod
    def dixon_coles_correction(
        home_goals: int,
        away_goals: int,
        home_xg: float,
        away_xg: float,
        rho: float,
    ) -> float:
        """
        Dixon-Coles tau correction.

        Only four scorelines are adjusted:

            0-0
            1-0
            0-1
            1-1
        """

        if home_goals == 0 and away_goals == 0:
            return 1.0 - (
                home_xg
                * away_xg
                * rho
            )

        if home_goals == 1 and away_goals == 0:
            return 1.0 + (
                away_xg
                * rho
            )

        if home_goals == 0 and away_goals == 1:
            return 1.0 + (
                home_xg
                * rho
            )

        if home_goals == 1 and away_goals == 1:
            return 1.0 - rho

        return 1.0

    # =============================================================
    # SCORE PROBABILITY
    # =============================================================

    def score_probability(
        self,
        home_goals: int,
        away_goals: int,
        home_xg: float,
        away_xg: float,
    ) -> float:
        """Calculate Dixon-Coles probability for an exact score."""

        home_probability = self.poisson_probability(
            home_goals,
            home_xg,
        )

        away_probability = self.poisson_probability(
            away_goals,
            away_xg,
        )

        correction = self.dixon_coles_correction(
            home_goals,
            away_goals,
            home_xg,
            away_xg,
            self.dixon_coles_rho,
        )

        return (
            home_probability
            * away_probability
            * correction
        )

    # =============================================================
    # MATCH PROBABILITIES
    # =============================================================

    def match_probabilities(
        self,
        home_team: str,
        away_team: str,
        max_goals: int = 10,
    ) -> dict[str, float]:
        """Calculate Dixon-Coles 1X2 probabilities."""

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

        # -------------------------------------------------
        # NORMALIZE
        # -------------------------------------------------

        total = (
            home_win
            + draw
            + away_win
        )

        if total > 0:

            home_win /= total
            draw /= total
            away_win /= total

        return {
            "home_win": home_win,
            "draw": draw,
            "away_win": away_win,
        }

    # =============================================================
    # PREDICT
    # =============================================================

    def predict(
        self,
        home_team: str,
        away_team: str,
    ) -> dict[str, float]:
        """Return xG and 1X2 probabilities."""

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