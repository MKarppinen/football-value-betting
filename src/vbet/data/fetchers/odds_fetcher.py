"""Fetch football bookmaker odds from The Odds API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv


class OddsFetcher:
    BASE_URL = "https://api.the-odds-api.com/v4"

    def __init__(
        self,
        sport: str = "soccer_epl",
        regions: str = "eu",
    ) -> None:
        load_dotenv(
            Path(__file__).resolve().parents[4] / ".env"
        )

        self.api_key = os.getenv("ODDS_API_KEY")

        if not self.api_key:
            raise ValueError(
                "ODDS_API_KEY puuttuu .env-tiedostosta."
            )

        self.sport = sport
        self.regions = regions

    def get_odds(self) -> list[dict[str, Any]]:
        url = f"{self.BASE_URL}/sports/{self.sport}/odds"

        params = {
            "apiKey": self.api_key,
            "regions": self.regions,
            "markets": "h2h",
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        }

        response = requests.get(
            url,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        return self._parse_events(data)

    @staticmethod
    def _parse_events(
        events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        matches = []

        for event in events:
            bookmakers = []

            for bookmaker in event.get("bookmakers", []):
                h2h_market = next(
                    (
                        market
                        for market in bookmaker.get("markets", [])
                        if market.get("key") == "h2h"
                    ),
                    None,
                )

                if h2h_market is None:
                    continue

                odds = {}

                for outcome in h2h_market.get("outcomes", []):
                    name = outcome.get("name")
                    price = outcome.get("price")

                    if name is None or price is None:
                        continue

                    odds[name] = float(price)

                bookmakers.append(
                    {
                        "key": bookmaker.get("key"),
                        "title": bookmaker.get("title"),
                        "last_update": bookmaker.get("last_update"),
                        "home_odds": odds.get(event["home_team"]),
                        "draw_odds": odds.get("Draw"),
                        "away_odds": odds.get(event["away_team"]),
                    }
                )

            matches.append(
                {
                    "event_id": event["id"],
                    "sport_key": event["sport_key"],
                    "commence_time": event["commence_time"],
                    "home_team": event["home_team"],
                    "away_team": event["away_team"],
                    "bookmakers": bookmakers,
                }
            )

        return matches