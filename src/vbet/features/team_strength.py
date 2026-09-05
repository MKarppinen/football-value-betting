"""Calculate opponent-adjusted home and away team strength."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from statistics import median


class TeamStrength:
    """
    Calculate separate home/away attacking and defensive strengths.

    Attack strength:
        Based on xG created, adjusted for opponent defensive strength.

    Defence strength:
        Based on xG conceded, adjusted for opponent attacking strength.

    rho controls how strongly opponent quality affects the adjustment.

    rho = 0:
        No opponent adjustment.

    rho = 0.5:
        Moderate adjustment.

    rho = 1:
        Full proportional adjustment.
    """

    def __init__(
        self,
        matches: Iterable[Mapping[str, object]],
        rho: float = 0.5,
    ) -> None:

        self.matches = list(matches)

        if not self.matches:
            raise ValueError(
                "Tietokannassa ei ole valmiita otteluita."
            )

        self.rho = rho

        # -----------------------------------------------------
        # RAW HOME / AWAY STATISTICS
        # -----------------------------------------------------

        home_scored = defaultdict(float)
        home_conceded = defaultdict(float)
        home_played = defaultdict(int)

        away_scored = defaultdict(float)
        away_conceded = defaultdict(float)
        away_played = defaultdict(int)

        for match in self.matches:

            home_team = str(match["home_team"])
            away_team = str(match["away_team"])

            home_xg = float(match["home_xg"])
            away_xg = float(match["away_xg"])

            # Home team
            home_scored[home_team] += home_xg
            home_conceded[home_team] += away_xg
            home_played[home_team] += 1

            # Away team
            away_scored[away_team] += away_xg
            away_conceded[away_team] += home_xg
            away_played[away_team] += 1

        # -----------------------------------------------------
        # RAW AVERAGES
        # -----------------------------------------------------

        self._home_scored = {
            team: home_scored[team] / home_played[team]
            for team in home_played
        }

        self._home_conceded = {
            team: home_conceded[team] / home_played[team]
            for team in home_played
        }

        self._away_scored = {
            team: away_scored[team] / away_played[team]
            for team in away_played
        }

        self._away_conceded = {
            team: away_conceded[team] / away_played[team]
            for team in away_played
        }

        # -----------------------------------------------------
        # LEAGUE MEDIANS
        # -----------------------------------------------------

        self.home_attack_median = median(
            self._home_scored.values()
        )

        self.away_attack_median = median(
            self._away_scored.values()
        )

        self.home_defence_median = median(
            self._home_conceded.values()
        )

        self.away_defence_median = median(
            self._away_conceded.values()
        )

        # -----------------------------------------------------
        # ADJUSTED STATISTICS
        # -----------------------------------------------------

        self._home_attack = {}
        self._away_attack = {}

        self._home_defence = {}
        self._away_defence = {}

        # These are accumulated from individual matches.
        home_attack_sum = defaultdict(float)
        home_defence_sum = defaultdict(float)
        home_adjusted_games = defaultdict(int)

        away_attack_sum = defaultdict(float)
        away_defence_sum = defaultdict(float)
        away_adjusted_games = defaultdict(int)

        # -----------------------------------------------------
        # MATCH-BY-MATCH OPPONENT ADJUSTMENT
        # -----------------------------------------------------

        for match in self.matches:

            home_team = str(match["home_team"])
            away_team = str(match["away_team"])

            home_xg = float(match["home_xg"])
            away_xg = float(match["away_xg"])

            # =================================================
            # HOME TEAM ATTACK
            # =================================================

            opponent_away_defence = self._away_conceded[
                away_team
            ]

            attack_factor = (
                self.away_defence_median
                / opponent_away_defence
            ) ** self.rho

            adjusted_home_xg = (
                home_xg * attack_factor
            )

            home_attack_sum[home_team] += adjusted_home_xg

            # =================================================
            # HOME TEAM DEFENCE
            # =================================================

            opponent_away_attack = self._away_scored[
                away_team
            ]

            defence_factor = (
                opponent_away_attack
                / self.away_attack_median
            ) ** self.rho

            adjusted_home_xga = (
                away_xg * defence_factor
            )

            home_defence_sum[home_team] += adjusted_home_xga

            home_adjusted_games[home_team] += 1

            # =================================================
            # AWAY TEAM ATTACK
            # =================================================

            opponent_home_defence = self._home_conceded[
                home_team
            ]

            attack_factor = (
                self.home_defence_median
                / opponent_home_defence
            ) ** self.rho

            adjusted_away_xg = (
                away_xg * attack_factor
            )

            away_attack_sum[away_team] += adjusted_away_xg

            # =================================================
            # AWAY TEAM DEFENCE
            # =================================================

            opponent_home_attack = self._home_scored[
                home_team
            ]

            defence_factor = (
                opponent_home_attack
                / self.home_attack_median
            ) ** self.rho

            adjusted_away_xga = (
                home_xg * defence_factor
            )

            away_defence_sum[away_team] += adjusted_away_xga

            away_adjusted_games[away_team] += 1

        # -----------------------------------------------------
        # FINAL ADJUSTED AVERAGES
        # -----------------------------------------------------

        for team in home_adjusted_games:

            self._home_attack[team] = (
                home_attack_sum[team]
                / home_adjusted_games[team]
            )

            self._home_defence[team] = (
                home_defence_sum[team]
                / home_adjusted_games[team]
            )

        for team in away_adjusted_games:

            self._away_attack[team] = (
                away_attack_sum[team]
                / away_adjusted_games[team]
            )

            self._away_defence[team] = (
                away_defence_sum[team]
                / away_adjusted_games[team]
            )

        # -----------------------------------------------------
        # OVERALL STRENGTH
        # -----------------------------------------------------

        teams = set(
            self._home_attack
        ) | set(
            self._away_attack
        )

        self._overall_attack = {}
        self._overall_defence = {}
        self._overall_strength = {}

        self._home_strength = {}
        self._away_strength = {}

        for team in teams:

            home_attack = self._home_attack.get(
                team,
                self._home_attack_median_fallback(),
            )

            away_attack = self._away_attack.get(
                team,
                self._away_attack_median_fallback(),
            )

            home_defence = self._home_defence.get(
                team,
                self._home_defence_median_fallback(),
            )

            away_defence = self._away_defence.get(
                team,
                self._away_defence_median_fallback(),
            )

            overall_attack = (
                home_attack + away_attack
            ) / 2

            overall_defence = (
                home_defence + away_defence
            ) / 2

            self._overall_attack[team] = overall_attack
            self._overall_defence[team] = overall_defence

            # Lower xGA = better defence.
            #
            # Convert defence into a positive strength
            # by comparing it with league median.

            attack_strength = (
                overall_attack
                / self._overall_attack_median()
            )

            defence_strength = (
                self._overall_defence_median()
                / overall_defence
            )

            self._overall_strength[team] = (
                attack_strength + defence_strength
            ) / 2

            # Home strength
            self._home_strength[team] = (
                (
                    home_attack
                    / self.home_attack_median
                )
                +
                (
                    self.home_defence_median
                    / home_defence
                )
            ) / 2

            # Away strength
            self._away_strength[team] = (
                (
                    away_attack
                    / self.away_attack_median
                )
                +
                (
                    self.away_defence_median
                    / away_defence
                )
            ) / 2

        # -----------------------------------------------------
        # 1-5 RANKING SCALE
        # -----------------------------------------------------

        self._overall_class = self._classes(
            self._overall_strength
        )

        self._home_class = self._classes(
            self._home_strength
        )

        self._away_class = self._classes(
            self._away_strength
        )

    # =========================================================
    # FALLBACKS
    # =========================================================

    def _home_attack_median_fallback(self) -> float:
        return self.home_attack_median

    def _away_attack_median_fallback(self) -> float:
        return self.away_attack_median

    def _home_defence_median_fallback(self) -> float:
        return self.home_defence_median

    def _away_defence_median_fallback(self) -> float:
        return self.away_defence_median

    def _overall_attack_median(self) -> float:
        return (
            self.home_attack_median
            + self.away_attack_median
        ) / 2

    def _overall_defence_median(self) -> float:
        return (
            self.home_defence_median
            + self.away_defence_median
        ) / 2

    # =========================================================
    # CLASSIFICATION
    # =========================================================

    @staticmethod
    def _classes(
        values: dict[str, float],
    ) -> dict[str, int]:

        if not values:
            return {}

        minimum = min(values.values())
        maximum = max(values.values())

        if maximum == minimum:
            return {
                team: 3
                for team in values
            }

        result = {}

        for team, value in values.items():

            normalized = (
                (value - minimum)
                / (maximum - minimum)
            )

            result[team] = min(
                5,
                max(
                    1,
                    int(normalized * 5) + 1,
                ),
            )

        return result

    # =========================================================
    # TEAM LIST
    # =========================================================

    def teams(self) -> list[str]:
        return sorted(
            self._overall_strength.keys()
        )

    # =========================================================
    # ATTACK
    # =========================================================

    def home_attack(self, team: str) -> float:
        return self._home_attack[team]

    def away_attack(self, team: str) -> float:
        return self._away_attack[team]

    def overall_attack(self, team: str) -> float:
        return self._overall_attack[team]

    # =========================================================
    # DEFENCE
    # =========================================================

    def home_defence(self, team: str) -> float:
        return self._home_defence[team]

    def away_defence(self, team: str) -> float:
        return self._away_defence[team]

    def overall_defence(self, team: str) -> float:
        return self._overall_defence[team]

    # =========================================================
    # STRENGTH
    # =========================================================

    def strength(self, team: str) -> float:
        return self._overall_strength[team]

    def home_strength(self, team: str) -> float:
        return self._home_strength[team]

    def away_strength(self, team: str) -> float:
        return self._away_strength[team]

    # =========================================================
    # CLASSES 1-5
    # =========================================================

    def strength_class(self, team: str) -> int:
        return self._overall_class[team]

    def home_strength_class(self, team: str) -> int:
        return self._home_class[team]

    def away_strength_class(self, team: str) -> int:
        return self._away_class[team]

    # =========================================================
    # 60/40 WEIGHTED VALUES
    # =========================================================

    def weighted_home_attack(
        self,
        team: str,
    ) -> float:

        return (
            0.60 * self.home_attack(team)
            + 0.40 * self.away_attack(team)
        )

    def weighted_away_attack(
        self,
        team: str,
    ) -> float:

        return (
            0.60 * self.away_attack(team)
            + 0.40 * self.home_attack(team)
        )

    def weighted_home_defence(
        self,
        team: str,
    ) -> float:

        return (
            0.60 * self.home_defence(team)
            + 0.40 * self.away_defence(team)
        )

    def weighted_away_defence(
        self,
        team: str,
    ) -> float:

        return (
            0.60 * self.away_defence(team)
            + 0.40 * self.home_defence(team)
        )

    # =========================================================
    # BACKWARDS COMPATIBILITY
    # =========================================================

    def home_scored_xg(self, team: str) -> float:
        return self.home_attack(team)

    def home_conceded_xg(self, team: str) -> float:
        return self.home_defence(team)

    def away_scored_xg(self, team: str) -> float:
        return self.away_attack(team)

    def away_conceded_xg(self, team: str) -> float:
        return self.away_defence(team)

    def overall_scored_xg(self, team: str) -> float:
        return self.overall_attack(team)

    def overall_conceded_xg(self, team: str) -> float:
        return self.overall_defence(team)