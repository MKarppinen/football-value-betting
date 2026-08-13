"""Command-line entry point for Valuebet."""
from __future__ import annotations

import argparse

from vbet.data.repository import MatchRepository
from vbet.data.updater import DataUpdater
from vbet.features.team_strength import TeamStrength
from vbet.models.poisson_model import PoissonModel


def main() -> None:
    parser = argparse.ArgumentParser(description="Football value-betting research tool")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("update", help="Download and store FBref historical matches")
    predict = sub.add_parser("predict", help="Calculate 1X2 probabilities from stored results")
    predict.add_argument("home_team"); predict.add_argument("away_team")
    args = parser.parse_args()
    if args.command == "update":
        print(f"Saved {DataUpdater().update_history()} historical matches.")
        return
    matches = MatchRepository().completed_matches()
    strengths = TeamStrength(matches)
    result = PoissonModel(strengths.league_average).predict(strengths.attack(args.home_team), strengths.defence(args.home_team), strengths.attack(args.away_team), strengths.defence(args.away_team))
    print(f"{args.home_team} win: {result['home']:.1%}")
    print(f"Draw: {result['draw']:.1%}")
    print(f"{args.away_team} win: {result['away']:.1%}")


if __name__ == "__main__":
    main()
