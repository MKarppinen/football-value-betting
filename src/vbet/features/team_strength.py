import numpy as np
class TeamStrength:
    def __init__(self, league: str, team_name: str) -> None:
        self.league = league
        self.team_name = team_name
        self.calculate_attack
        self.calculate_defense
    def calculate_attack(self, expected_goals: float, matches_played: int) -> float:
        expected_goals_per_match = expected_goals / matches_played
        attack_strength = expected_goals_per_match / #self.get_league_avg_expected_goals()#
        return attack_strength
     def calculate_defense(self, expected_goalsA: float, matches_played: int) -> float:
        expected_goalsA_per_match = expected_goalsA / matches_played
        defense_strength = expected_goals_per_match / #self.get_league_avg_expected_goalsA()#
        return defense_strength
    