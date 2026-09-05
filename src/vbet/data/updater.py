"""Application service for updating football data and bookmaker odds."""
from __future__ import annotations

from datetime import datetime

from vbet.data.fetchers.odds_fetcher import OddsFetcher
from vbet.data.fetchers.understat_fetcher import UnderstatFetcher
from vbet.data.repository import MatchRepository


class DataUpdater:
    def __init__(
        self,
        repository: MatchRepository | None = None,
    ) -> None:
        self.repository = repository or MatchRepository()

    def update_history(self) -> int:
        """Download and save historical Understat matches."""
        return self.repository.save_matches(
            UnderstatFetcher().get_matches()
        )

    def update_odds(self) -> int:
        """Download and save upcoming bookmaker odds."""
        events = OddsFetcher().get_odds()

        saved_odds = 0

        for event in events:
            commence_time = event.get("commence_time")

            if not commence_time:
                continue

            match_date = datetime.fromisoformat(
                commence_time.replace("Z", "+00:00")
            ).date().isoformat()

            match_id = self.repository.save_scheduled_match(
                {
                    "competition": "Premier League",
                    "country": "England",
                    "date": match_date,
                    "home_team": event["home_team"],
                    "away_team": event["away_team"],
                    "season": "",
                    "status": "scheduled",
                    "source": "odds_api",
                    "source_match_id": event["event_id"],
                }
            )

            saved_odds += self.repository.save_odds(
                match_id,
                event.get("bookmakers", []),
            )

        return saved_odds

    def update_all(self) -> tuple[int, int]:
        """Update historical matches and bookmaker odds."""
        historical_matches = self.update_history()
        odds = self.update_odds()

        return historical_matches, odds