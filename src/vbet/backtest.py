"""Walk-forward backtest for the Valuebet baseline model."""

from __future__ import annotations

import math
from typing import Any

from vbet.data.repository import MatchRepository
from vbet.features.team_strength import TeamStrength
from vbet.models.poisson_model import PoissonModel


MIN_HISTORY = 5

# =============================================================
# BASELINE PARAMETERS
# =============================================================

TEAM_STRENGTH_RHO = 0.50

HOME_ADVANTAGE = 1.14

DIXON_COLES_RHO = -0.25


# =============================================================
# ACTUAL OUTCOME
# =============================================================

def actual_outcome(
    match: dict[str, Any],
) -> int:
    """
    Return:

        0 = home win
        1 = draw
        2 = away win
    """

    home_goals = int(
        match["home_goals"]
    )

    away_goals = int(
        match["away_goals"]
    )

    if home_goals > away_goals:
        return 0

    if home_goals == away_goals:
        return 1

    return 2


# =============================================================
# BRIER SCORE
# =============================================================

def brier_score(
    probabilities: list[
        tuple[float, float, float]
    ],
    outcomes: list[int],
) -> float:
    """Calculate multiclass Brier score."""

    total = 0.0

    for probs, outcome in zip(
        probabilities,
        outcomes,
    ):

        for index, probability in enumerate(
            probs
        ):

            actual = (
                1.0
                if index == outcome
                else 0.0
            )

            total += (
                probability - actual
            ) ** 2

    return total / len(
        probabilities
    )


# =============================================================
# LOG LOSS
# =============================================================

def log_loss(
    probabilities: list[
        tuple[float, float, float]
    ],
    outcomes: list[int],
) -> float:
    """Calculate multiclass logarithmic loss."""

    total = 0.0

    for probs, outcome in zip(
        probabilities,
        outcomes,
    ):

        probability = max(
            min(
                probs[outcome],
                1.0 - 1e-15,
            ),
            1e-15,
        )

        total -= math.log(
            probability
        )

    return total / len(
        probabilities
    )


# =============================================================
# CALIBRATION
# =============================================================

def calibration_table(
    probabilities: list[
        tuple[float, float, float]
    ],
    outcomes: list[int],
) -> None:
    """Print calibration for Home, Draw and Away."""

    print()

    print(
        "=" * 90
    )

    print(
        "CALIBRATION"
    )

    print(
        "=" * 90
    )

    labels = [
        "HOME",
        "DRAW",
        "AWAY",
    ]

    for outcome_index, label in enumerate(
        labels
    ):

        print()

        print(
            label
        )

        print(
            "-" * 90
        )

        print(
            f"{'PREDICTED':<15}"
            f"{'ACTUAL':<15}"
            f"{'GAMES':>10}"
        )

        for lower in range(
            0,
            100,
            10,
        ):

            upper = lower + 10

            selected = []

            for probs, actual in zip(
                probabilities,
                outcomes,
            ):

                probability = (
                    probs[outcome_index]
                    * 100
                )

                if (
                    probability >= lower
                    and probability < upper
                ):

                    selected.append(
                        actual == outcome_index
                    )

            if not selected:
                continue

            actual_rate = (
                sum(selected)
                / len(selected)
                * 100
            )

            print(
                f"{lower:>2}-{upper:<2}%"
                f"{'':<10}"
                f"{actual_rate:>6.1f}%"
                f"{'':<9}"
                f"{len(selected):>10}"
            )


# =============================================================
# RUN BACKTEST
# =============================================================

def run_backtest(
    competition: str = "ENG-Premier League",
) -> None:
    """Run the final baseline walk-forward backtest."""

    repository = MatchRepository()

    matches = repository.completed_matches(
        competition=competition,
    )

    if not matches:

        print(
            "No completed matches found."
        )

        return

    print()

    print(
        "=" * 90
    )

    print(
        "VALUEBET BASELINE WALK-FORWARD BACKTEST"
    )

    print(
        "=" * 90
    )

    print()

    print(
        f"Competition:          {competition}"
    )

    print(
        f"Historical matches:   {len(matches)}"
    )

    print(
        f"Minimum history:      {MIN_HISTORY}"
    )

    print(
        f"TeamStrength rho:     {TEAM_STRENGTH_RHO:.2f}"
    )

    print(
        f"Home advantage:       {HOME_ADVANTAGE:.2f}"
    )

    print(
        f"Dixon-Coles rho:      {DIXON_COLES_RHO:.2f}"
    )

    print(
        "Home/Away weighting:   60/40"
    )

    print(
        "Dixon-Coles:           enabled"
    )

    probabilities: list[
        tuple[float, float, float]
    ] = []

    outcomes: list[int] = []

    skipped = 0

    # =========================================================
    # WALK FORWARD
    # =========================================================

    for index, match in enumerate(
        matches
    ):

        # Only data before the target
        # match may be used.

        history = matches[:index]

        if len(history) < MIN_HISTORY:

            skipped += 1

            continue

        home_team = str(
            match["home_team"]
        )

        away_team = str(
            match["away_team"]
        )

        try:

            strengths = TeamStrength(
                history,
                rho=TEAM_STRENGTH_RHO,
            )

            # Both teams need historical data.

            strengths.home_attack(
                home_team
            )

            strengths.away_attack(
                away_team
            )

            model = PoissonModel(
                strengths,
                home_advantage=HOME_ADVANTAGE,
                dixon_coles_rho=DIXON_COLES_RHO,
            )

            result = model.predict(
                home_team,
                away_team,
            )

        except (
            KeyError,
            ValueError,
            ZeroDivisionError,
        ):

            skipped += 1

            continue

        probs = (
            float(result["home_win"]),
            float(result["draw"]),
            float(result["away_win"]),
        )

        probabilities.append(
            probs
        )

        outcomes.append(
            actual_outcome(match)
        )

    # =========================================================
    # RESULTS
    # =========================================================

    if not probabilities:

        print()

        print(
            "No matches could be tested."
        )

        return

    score = brier_score(
        probabilities,
        outcomes,
    )

    loss = log_loss(
        probabilities,
        outcomes,
    )

    tested = len(
        probabilities
    )

    print()

    print(
        "=" * 90
    )

    print(
        "BASELINE RESULTS"
    )

    print(
        "=" * 90
    )

    print()

    print(
        f"Matches tested:       {tested}"
    )

    print(
        f"Matches skipped:      {skipped}"
    )

    print(
        f"Brier Score:          {score:.4f}"
    )

    print(
        f"Log Loss:             {loss:.4f}"
    )

    # =========================================================
    # OUTCOME PERFORMANCE
    # =========================================================

    labels = [
        "Home",
        "Draw",
        "Away",
    ]

    print()

    print(
        "=" * 90
    )

    print(
        "OUTCOME PERFORMANCE"
    )

    print(
        "=" * 90
    )

    print(
        f"{'OUTCOME':<15}"
        f"{'MODEL AVG':>15}"
        f"{'ACTUAL RATE':>15}"
        f"{'GAMES':>10}"
    )

    print(
        "-" * 90
    )

    for outcome_index, label in enumerate(
        labels
    ):

        model_average = (
            sum(
                probs[outcome_index]
                for probs in probabilities
            )
            / len(probabilities)
        )

        actual_rate = (
            sum(
                outcome == outcome_index
                for outcome in outcomes
            )
            / len(outcomes)
        )

        games = sum(
            outcome == outcome_index
            for outcome in outcomes
        )

        print(
            f"{label:<15}"
            f"{model_average:>14.1%}"
            f"{actual_rate:>14.1%}"
            f"{games:>10}"
        )

    # =========================================================
    # CALIBRATION
    # =========================================================

    calibration_table(
        probabilities,
        outcomes,
    )

    # =========================================================
    # COMPLETE
    # =========================================================

    print()

    print(
        "=" * 90
    )

    print(
        "BASELINE BACKTEST COMPLETE"
    )

    print(
        "=" * 90
    )