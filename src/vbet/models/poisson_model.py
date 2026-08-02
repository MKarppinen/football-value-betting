import numpy as np
from scipy.stats import poisson
class PoissonModel:
    def __init__(self, avg_goals_per_match: float, home_advantage: float = 1.35, max_goals: int = 10) -> None:
        self.avg_goals_per_match = avg_goals_per_match
        self.home_advantage = home_advantage
        self.max_goals = max_goals

    def calculate_probabilities(self, home_lambda: float, away_lambda: float) -> np.ndarray:
        goals = np.arange(0, self.max_goals + 1)
        home_probs = poisson.pmf(goals, home_lambda)
        away_probs = poisson.pmf(goals, away_lambda)
        matrix  = np.outer(home_probs, away_probs)
        total = matrix.sum()
        if total < 0.999:
            print("Warning: The total probability is less than 0.999, which may indicate an issue with the model parameters.")
        return matrix
