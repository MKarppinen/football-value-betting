"""Command-line entry point for Valuebet."""

from __future__ import annotations

import argparse

from vbet.data.repository import MatchRepository
from vbet.data.updater import DataUpdater
from vbet.features.team_strength import TeamStrength
from vbet.models.poisson_model import PoissonModel


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Football value-betting research tool"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "update",
        help="Download and store historical matches",
    )

    predict = sub.add_parser(
        "predict",
        help="Calculate 1X2 probabilities from stored xG data",
    )

    predict.add_argument("home_team")
    predict.add_argument("away_team")

    args = parser.parse_args()

    if args.command == "update":
        print(
            f"Saved {DataUpdater().update_history()} "
            "historical matches."
        )
        return

    matches = MatchRepository().completed_matches()

    strengths = TeamStrength(matches)
    model = PoissonModel(strengths)

    result = model.predict(
        args.home_team,
        args.away_team,
    )

    print()
    print(f"{args.home_team} vs {args.away_team}")
    print("-" * 45)

    print(
        f"{args.home_team} home scored xG: "
        f"{strengths.home_scored_xg(args.home_team):.3f}"
    )

    print(
        f"{args.home_team} home conceded xG: "
        f"{strengths.home_conceded_xg(args.home_team):.3f}"
    )

    print(
        f"{args.away_team} away scored xG: "
        f"{strengths.away_scored_xg(args.away_team):.3f}"
    )

    print(
        f"{args.away_team} away conceded xG: "
        f"{strengths.away_conceded_xg(args.away_team):.3f}"
    )

    print()
    print(f"Expected {args.home_team} xG: {result['home_xg']:.3f}")
    print(f"Expected {args.away_team} xG: {result['away_xg']:.3f}")

    print()
    print(f"{args.home_team} win: {result['home_win']:.1%}")
    print(f"Fair odds: {1 / result['home_win']:.2f}")

    print()
    print(f"Draw: {result['draw']:.1%}")
    print(f"Fair odds: {1 / result['draw']:.2f}")

    print()
    print(f"{args.away_team} win: {result['away_win']:.1%}")
    print(f"Fair odds: {1 / result['away_win']:.2f}")

    total = (
        result["home_win"]
        + result["draw"]
        + result["away_win"]
    )

    print()
    print(f"Probability total: {total:.1%}")


if __name__ == "__main__":
    main()