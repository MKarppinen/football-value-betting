import os
from datetime import date, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

from vbet.data.repository import MatchRepository


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
        """Hakee kaikki ottelut."""
        return self._get("matches")

    def get_upcoming_matches(self, competition: str = "PL"):
        """Hakee seuraavan viikon ottelut valitusta sarjasta."""
        today = date.today()
        next_week = today + timedelta(days=7)

        return self._get(
            f"competitions/{competition}/matches",
            params={
                "dateFrom": today.isoformat(),
                "dateTo": next_week.isoformat(),
            },
        )

    def print_matches(self, competition: str = "PL"):
        """Tulostaa seuraavan viikon ottelut."""
        data = self.get_upcoming_matches(competition)
        matches = data.get("matches", [])

        print(f"Found {len(matches)} matches\n")

        for match in matches:
            print(
                f"{match['homeTeam']['name']} vs "
                f"{match['awayTeam']['name']}"
            )

    def save_upcoming_matches(self, competition: str = "PL"):
        """Tallentaa seuraavan viikon ottelut tietokantaan."""
        data = self.get_upcoming_matches(competition)

        print(f"API returned {data.get('count', 0)} matches")

        matches = data.get("matches", [])

        repository = MatchRepository()

        for match in matches:
            score = match.get("score", {})
            repository.save_match({
                "competition": match["competition"]["name"],
                "country": match["competition"].get("area", {}).get("name"),
                "date": match["utcDate"][:10],
                "home_team": match["homeTeam"]["name"],
                "away_team": match["awayTeam"]["name"],
                "home_goals": score.get("fullTime", {}).get("home"),
                "away_goals": score.get("fullTime", {}).get("away"),
                "status": match["status"].lower(),
                "source": "football-data",
                "source_match_id": str(match["id"]),
            })

        print(f"Saved {len(matches)} matches to database.")


    
