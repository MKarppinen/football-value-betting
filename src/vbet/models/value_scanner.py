"""Find value bets by comparing model probabilities with bookmaker odds."""

from __future__ import annotations

from typing import Any


class ValueScanner:
    def __init__(self, min_ev: float = 0.0) -> None:
        """
        min_ev:
            Minimum expected value required to report a bet.

            Example:
                min_ev=0.05 means only bets with at least +5% EV
                are returned.
        """
        self.min_ev = min_ev

    @staticmethod
    def fair_odds(probability: float) -> float:
        """Convert a probability into fair decimal odds."""

        if probability <= 0:
            return float("inf")

        return 1.0 / probability

    @staticmethod
    def expected_value(
        probability: float,
        odds: float,
    ) -> float:
        """
        Calculate expected value.

        EV = probability * decimal odds - 1
        """

        return probability * odds - 1.0

    def scan_match(
        self,
        home_team: str,
        away_team: str,
        probabilities: dict[str, float],
        bookmakers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Compare model probabilities against bookmaker odds.

        Returns one entry per outcome.

        Each entry contains the top 5 bookmaker odds for that
        outcome, sorted by highest odds.
        """

        outcomes = {
            "home": {
                "probability": probabilities["home_win"],
                "label": home_team,
            },
            "draw": {
                "probability": probabilities["draw"],
                "label": "Draw",
            },
            "away": {
                "probability": probabilities["away_win"],
                "label": away_team,
            },
        }

        value_bets: list[dict[str, Any]] = []

        for outcome, data in outcomes.items():

            probability = float(data["probability"])

            if probability <= 0:
                continue

            fair_odds = self.fair_odds(probability)

            bookmaker_odds: list[dict[str, Any]] = []

            for bookmaker in bookmakers:

                if outcome == "home":
                    odds = bookmaker.get("home_odds")

                elif outcome == "draw":
                    odds = bookmaker.get("draw_odds")

                else:
                    odds = bookmaker.get("away_odds")

                if odds is None:
                    continue

                try:
                    odds = float(odds)
                except (TypeError, ValueError):
                    continue

                if odds <= 1.0:
                    continue

                ev = self.expected_value(
                    probability,
                    odds,
                )

                if ev < self.min_ev:
                    continue

                bookmaker_name = bookmaker.get("title")

                if not bookmaker_name:
                    bookmaker_name = bookmaker.get(
                        "key",
                        "Unknown",
                    )

                bookmaker_odds.append(
                    {
                        "bookmaker": bookmaker_name,
                        "odds": odds,
                        "ev": ev,
                    }
                )

            if not bookmaker_odds:
                continue

            # Highest odds first.
            bookmaker_odds.sort(
                key=lambda item: item["odds"],
                reverse=True,
            )

            # Only show the five best bookmaker odds.
            top_5 = bookmaker_odds[:5]

            best = top_5[0]

            value_bets.append(
                {
                    "home_team": home_team,
                    "away_team": away_team,
                    "outcome": outcome,
                    "label": data["label"],
                    "probability": probability,
                    "fair_odds": fair_odds,
                    "best_bookmaker": best["bookmaker"],
                    "best_odds": best["odds"],
                    "best_ev": best["ev"],
                    "top_bookmakers": top_5,
                }
            )

        # Highest EV first.
        value_bets.sort(
            key=lambda bet: bet["best_ev"],
            reverse=True,
        )

        return value_bets