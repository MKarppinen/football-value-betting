"""Command-line entry point for Valuebet."""

from __future__ import annotations

import argparse

from vbet.backtest import run_backtest
from vbet.data.repository import MatchRepository
from vbet.data.updater import DataUpdater
from vbet.features.team_strength import TeamStrength
from vbet.models.poisson_model import PoissonModel
from vbet.models.value_scanner import ValueScanner


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Football value-betting research tool"
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # =========================================================
    # UPDATE
    # =========================================================

    sub.add_parser(
        "update",
        help="Download historical matches and bookmaker odds",
    )

    # =========================================================
    # PREDICT
    # =========================================================

    predict = sub.add_parser(
        "predict",
        help="Calculate 1X2 probabilities",
    )

    predict.add_argument(
        "home_team",
    )

    predict.add_argument(
        "away_team",
    )

    # =========================================================
    # SCAN
    # =========================================================

    scan = sub.add_parser(
        "scan",
        help="Scan upcoming matches for value bets",
    )

    scan.add_argument(
        "--min-ev",
        type=float,
        default=0.0,
        help="Minimum expected value, e.g. 0.05 = +5%",
    )

    # =========================================================
    # TEAMS
    # =========================================================

    sub.add_parser(
        "teams",
        help="Show team strength rankings",
    )

    # =========================================================
    # BACKTEST
    # =========================================================

    backtest = sub.add_parser(
        "backtest",
        help="Run walk-forward historical backtest",
    )

    backtest.add_argument(
        "--competition",
        default="ENG-Premier League",
        help="Competition to backtest",
    )

    args = parser.parse_args()

    repository = MatchRepository()

    # =========================================================
    # UPDATE
    # =========================================================

    if args.command == "update":

        historical, odds = DataUpdater().update_all()

        print(
            f"Saved {historical} historical matches."
        )

        print(
            f"Saved {odds} bookmaker odds."
        )

        return

    # =========================================================
    # PREDICT
    # =========================================================

    if args.command == "predict":

        matches = repository.completed_matches()

        if not matches:

            print(
                "No completed matches found."
            )

            return

        strengths = TeamStrength(
            matches,
            rho=0.5,
        )

        model = PoissonModel(
            strengths,
        )

        try:

            result = model.predict(
                args.home_team,
                args.away_team,
            )

        except KeyError as error:

            print()

            print(
                f"Team missing from historical data: {error}"
            )

            return

        print()

        print(
            f"{args.home_team} vs "
            f"{args.away_team}"
        )

        print(
            "=" * 80
        )

        print()

        print(
            f"Expected {args.home_team} xG: "
            f"{result['home_xg']:.3f}"
        )

        print(
            f"Expected {args.away_team} xG: "
            f"{result['away_xg']:.3f}"
        )

        print()

        print(
            "RESULT PROBABILITIES"
        )

        print(
            "-" * 80
        )

        print(
            f"1  {args.home_team:<30}"
            f"{result['home_win']:>7.1%}"
            f"   Fair odds: "
            f"{1 / result['home_win']:.2f}"
        )

        print(
            f"X  {'Draw':<30}"
            f"{result['draw']:>7.1%}"
            f"   Fair odds: "
            f"{1 / result['draw']:.2f}"
        )

        print(
            f"2  {args.away_team:<30}"
            f"{result['away_win']:>7.1%}"
            f"   Fair odds: "
            f"{1 / result['away_win']:.2f}"
        )

        print()

        total = (
            result["home_win"]
            + result["draw"]
            + result["away_win"]
        )

        print(
            f"Probability total: {total:.1%}"
        )

        return

    # =========================================================
    # TEAMS
    # =========================================================

    if args.command == "teams":

        matches = repository.completed_matches()

        if not matches:

            print(
                "No completed matches found."
            )

            return

        strengths = TeamStrength(
            matches,
            rho=0.5,
        )

        # -----------------------------------------------------
        # OVERALL
        # -----------------------------------------------------

        overall = []

        for team in strengths.teams():

            overall.append(
                {
                    "team": team,
                    "attack": strengths.overall_attack(team),
                    "defence": strengths.overall_defence(team),
                    "strength": strengths.strength(team),
                    "class": strengths.strength_class(team),
                }
            )

        overall.sort(
            key=lambda x: x["strength"],
            reverse=True,
        )

        print()

        print(
            "=" * 95
        )

        print(
            "OVERALL TEAM STRENGTH"
        )

        print(
            "=" * 95
        )

        print(
            f"{'TEAM':<30}"
            f"{'ATTACK':>12}"
            f"{'DEFENCE':>12}"
            f"{'STRENGTH':>12}"
            f"{'CLASS':>8}"
        )

        print(
            "-" * 95
        )

        for row in overall:

            print(
                f"{row['team']:<30}"
                f"{row['attack']:>12.2f}"
                f"{row['defence']:>12.2f}"
                f"{row['strength']:>12.2f}"
                f"{row['class']:>8}"
            )

        # -----------------------------------------------------
        # HOME
        # -----------------------------------------------------

        home = []

        for team in strengths.teams():

            home.append(
                {
                    "team": team,
                    "attack": strengths.home_attack(team),
                    "defence": strengths.home_defence(team),
                    "strength": strengths.home_strength(team),
                    "class": strengths.home_strength_class(team),
                }
            )

        home.sort(
            key=lambda x: x["strength"],
            reverse=True,
        )

        print()

        print(
            "=" * 95
        )

        print(
            "HOME TEAM STRENGTH"
        )

        print(
            "=" * 95
        )

        print(
            f"{'TEAM':<30}"
            f"{'ATTACK':>12}"
            f"{'DEFENCE':>12}"
            f"{'STRENGTH':>12}"
            f"{'CLASS':>8}"
        )

        print(
            "-" * 95
        )

        for row in home:

            print(
                f"{row['team']:<30}"
                f"{row['attack']:>12.2f}"
                f"{row['defence']:>12.2f}"
                f"{row['strength']:>12.2f}"
                f"{row['class']:>8}"
            )

        # -----------------------------------------------------
        # AWAY
        # -----------------------------------------------------

        away = []

        for team in strengths.teams():

            away.append(
                {
                    "team": team,
                    "attack": strengths.away_attack(team),
                    "defence": strengths.away_defence(team),
                    "strength": strengths.away_strength(team),
                    "class": strengths.away_strength_class(team),
                }
            )

        away.sort(
            key=lambda x: x["strength"],
            reverse=True,
        )

        print()

        print(
            "=" * 95
        )

        print(
            "AWAY TEAM STRENGTH"
        )

        print(
            "=" * 95
        )

        print(
            f"{'TEAM':<30}"
            f"{'ATTACK':>12}"
            f"{'DEFENCE':>12}"
            f"{'STRENGTH':>12}"
            f"{'CLASS':>8}"
        )

        print(
            "-" * 95
        )

        for row in away:

            print(
                f"{row['team']:<30}"
                f"{row['attack']:>12.2f}"
                f"{row['defence']:>12.2f}"
                f"{row['strength']:>12.2f}"
                f"{row['class']:>8}"
            )

        return

    # =========================================================
    # BACKTEST
    # =========================================================

    if args.command == "backtest":

        run_backtest(
            competition=args.competition,
        )

        return

    # =========================================================
    # SCAN
    # =========================================================

    if args.command == "scan":

        completed = repository.completed_matches()

        if not completed:

            print(
                "No completed matches found."
            )

            return

        strengths = TeamStrength(
            completed,
            rho=0.5,
        )

        model = PoissonModel(
            strengths,
        )

        scanner = ValueScanner(
            min_ev=args.min_ev,
        )

        upcoming = repository.upcoming_matches()

        if not upcoming:

            print(
                "No upcoming matches with bookmaker odds found."
            )

            return

        all_value_bets: list[dict] = []

        for match in upcoming:

            home_team = match[
                "home_team"
            ]

            away_team = match[
                "away_team"
            ]

            try:

                probabilities = (
                    model.match_probabilities(
                        home_team,
                        away_team,
                    )
                )

            except KeyError as error:

                print()

                print(
                    f"Skipping "
                    f"{home_team} vs "
                    f"{away_team}: "
                    f"team missing from "
                    f"historical data: "
                    f"{error}"
                )

                continue

            value_bets = scanner.scan_match(
                home_team,
                away_team,
                probabilities,
                match["bookmakers"],
            )

            all_value_bets.extend(
                value_bets
            )

        all_value_bets.sort(
            key=lambda bet: bet["ev"],
            reverse=True,
        )

        print()

        print(
            "=" * 80
        )

        print(
            "VALUEBET SCANNER"
        )

        print(
            "=" * 80
        )

        if not all_value_bets:

            print()

            print(
                "No value bets found."
            )

            return

        for bet in all_value_bets:

            print()

            print(
                f"{bet['home_team']} vs "
                f"{bet['away_team']}"
            )

            print(
                f"Outcome:             "
                f"{bet['label']}"
            )

            print(
                f"Bookmaker:           "
                f"{bet['bookmaker']}"
            )

            print(
                f"Market odds:         "
                f"{bet['odds']:.2f}"
            )

            print(
                f"Model probability:   "
                f"{bet['probability']:.1%}"
            )

            print(
                f"Fair odds:           "
                f"{bet['fair_odds']:.2f}"
            )

            print(
                f"EV:                  "
                f"{bet['ev']:+.1%}"
            )

            print(
                "-" * 80
            )


if __name__ == "__main__":
    main()