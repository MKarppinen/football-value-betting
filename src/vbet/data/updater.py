"""Application service for updating historical football data."""
from vbet.data.fetchers.understat_fetcher import UnderstatFetcher
from vbet.data.repository import MatchRepository


class DataUpdater:
    def __init__(self, repository: MatchRepository | None = None) -> None:
        self.repository = repository or MatchRepository()

    def update_history(self) -> int:
        return self.repository.save_matches(
            UnderstatFetcher().get_matches()
        )