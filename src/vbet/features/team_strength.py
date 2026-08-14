"""Calculate home and away xG averages from historical matches."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping


class TeamStrength:
    def __init__(self, matches: Iterable[Mapping[str, object]]) -> None:
        self.matches = list(matches)

        if not self.matches:
            raise ValueError("Tietokannassa ei ole valmiita otteluita.")

        # Home team statistics
        home_scored_xg = defaultdict(float)
        home_conceded_xg = defaultdict(float)
        home_played = defaultdict(int)

        # Away team statistics
        away_scored_xg = defaultdict(float)
        away_conceded_xg = defaultdict(float)
        away_played = defaultdict(int)

        for match in self.matches:
            home_team = str(match["home_team"])
            away_team = str(match["away_team"])

            home_xg = float(match["home_xg"])
            away_xg = float(match["away_xg"])

            # Home team's home statistics
            home_scored_xg[home_team] += home_xg
            home_conceded_xg[home_team] += away_xg
            home_played[home_team] += 1

            # Away team's away statistics
            away_scored_xg[away_team] += away_xg
            away_conceded_xg[away_team] += home_xg
            away_played[away_team] += 1

        self._home_scored_xg = {}
        self._home_conceded_xg = {}
        self._away_scored_xg = {}
        self._away_conceded_xg = {}

        # Average xG at home
        for team, matches_played in home_played.items():
            self._home_scored_xg[team] = (
                home_scored_xg[team] / matches_played
            )

            self._home_conceded_xg[team] = (
                home_conceded_xg[team] / matches_played
            )

        # Average xG away
        for team, matches_played in away_played.items():
            self._away_scored_xg[team] = (
                away_scored_xg[team] / matches_played
            )

            self._away_conceded_xg[team] = (
                away_conceded_xg[team] / matches_played
            )

    def home_scored_xg(self, team: str) -> float:
        return self._home_scored_xg[team]

    def home_conceded_xg(self, team: str) -> float:
        return self._home_conceded_xg[team]

    def away_scored_xg(self, team: str) -> float:
        return self._away_scored_xg[team]

    def away_conceded_xg(self, team: str) -> float:
        return self._away_conceded_xg[team]