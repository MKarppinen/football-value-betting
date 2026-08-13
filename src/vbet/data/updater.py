"""Application service for updating the historical database."""
from vbet.data.fetchers.fbref_fetcher import FBrefFetcher
from vbet.data.repository import MatchRepository


class DataUpdater:
    def __init__(self, repository: MatchRepository | None = None) -> None:
        self.repository = repository or MatchRepository()

    def update_history(self) -> int:
        return self.repository.save_matches(FBrefFetcher().get_matches())
