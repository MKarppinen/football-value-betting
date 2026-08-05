import os
from pathlib import Path

import requests
from dotenv import load_dotenv


class FootballDataFetcher:
    BASE_URL = "https://api.football-data.org/v4"

    def __init__(self):
        # Lataa .env projektin juuresta
        project_root = Path(__file__).resolve().parents[4]
        load_dotenv(project_root / ".env")

        self.api_key = os.getenv("FOOTBALL_DATA_API_KEY")

        if not self.api_key:
            raise ValueError("FOOTBALL_DATA_API_KEY not found in .env")

        self.headers = {
            "X-Auth-Token": self.api_key
        }

    def _get(self, endpoint: str, params: dict | None = None):
        response = requests.get(
            f"{self.BASE_URL}/{endpoint}",
            headers=self.headers,
            params=params,
            timeout=30,
        )

        response.raise_for_status()

        return response.json()

    def get_matches(self):
        """Hakee tämän päivän ottelut."""
        return self._get("matches")

    def get_upcoming_matches(self, competition: str = "PL"):
        """Hakee tulevat ottelut yhdestä sarjasta."""
        return self._get(
            f"competitions/{competition}/matches",
            params={"status": "SCHEDULED"},
        )

    def print_matches(self, competition: str = "PL"):
        data = self.get_upcoming_matches(competition)

        matches = data.get("matches", [])

        print(f"Found {len(matches)} matches\n")

        for match in matches:
            print(
                f"{match['homeTeam']['name']} vs "
                f"{match['awayTeam']['name']}"
            )

    