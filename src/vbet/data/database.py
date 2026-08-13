"""SQLite database used by the Valuebet application."""
from __future__ import annotations

import sqlite3
from pathlib import Path


class Database:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else Path(__file__).resolve().parents[3] / "football.db"

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize(self) -> None:
        with self.connect() as connection:
            self._migrate_legacy_schema(connection)
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS competitions (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL, country TEXT,
                    UNIQUE(name, country)
                );
                CREATE TABLE IF NOT EXISTS teams (
                    id INTEGER PRIMARY KEY, name TEXT NOT NULL,
                    competition_id INTEGER NOT NULL REFERENCES competitions(id),
                    UNIQUE(name, competition_id)
                );
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY, competition_id INTEGER NOT NULL REFERENCES competitions(id),
                    match_date TEXT NOT NULL, home_team_id INTEGER NOT NULL REFERENCES teams(id),
                    away_team_id INTEGER NOT NULL REFERENCES teams(id), home_goals INTEGER,
                    away_goals INTEGER, season TEXT, status TEXT NOT NULL DEFAULT 'scheduled',
                    source TEXT NOT NULL, source_match_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(competition_id, match_date, home_team_id, away_team_id),
                    UNIQUE(source, source_match_id)
                );
                CREATE TABLE IF NOT EXISTS match_stats (
                    match_id INTEGER PRIMARY KEY REFERENCES matches(id) ON DELETE CASCADE,
                    home_xg REAL, away_xg REAL, home_shots INTEGER, away_shots INTEGER,
                    home_shots_on_target INTEGER, away_shots_on_target INTEGER,
                    home_possession REAL, away_possession REAL, home_passes INTEGER, away_passes INTEGER,
                    home_pass_accuracy REAL, away_pass_accuracy REAL, home_yellow INTEGER,
                    away_yellow INTEGER, home_red INTEGER, away_red INTEGER,
                    home_corners INTEGER, away_corners INTEGER
                );
                CREATE TABLE IF NOT EXISTS odds (
                    id INTEGER PRIMARY KEY, match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                    bookmaker TEXT NOT NULL, market TEXT NOT NULL DEFAULT '1x2',
                    home_odds REAL, draw_odds REAL, away_odds REAL,
                    fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
                CREATE INDEX IF NOT EXISTS idx_matches_competition_date ON matches(competition_id, match_date);
                CREATE INDEX IF NOT EXISTS idx_odds_match ON odds(match_id);
            """)

    @staticmethod
    def _migrate_legacy_schema(connection: sqlite3.Connection) -> None:
        """Keep an old pre-relational database from blocking the new schema.

        Early Valuebet versions used a flat ``matches`` table with ``utc_date``.
        Its rows are retained in ``legacy_matches`` for reference; new data is
        written to the normalized tables created by :meth:`initialize`.
        """
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='matches'"
        ).fetchone()
        if not exists:
            return
        columns = {row[1] for row in connection.execute("PRAGMA table_info(matches)")}
        if "match_date" in columns:
            return
        connection.execute("DROP INDEX IF EXISTS idx_matches_date")
        connection.execute("ALTER TABLE matches RENAME TO legacy_matches")
