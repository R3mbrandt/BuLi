"""
Poisson-based Match Prediction Model
Predicts match outcomes using Poisson distribution for goal probabilities
"""

import numpy as np
import pandas as pd
from scipy.stats import poisson
from typing import Dict, Tuple, Optional, List
from itertools import product


class PoissonMatchPredictor:
    """
    Predicts football match outcomes using Poisson distribution

    The model assumes:
    - Goals scored by each team follow a Poisson distribution
    - Goal scoring is independent between teams
    - Lambda (expected goals) is influenced by team strength and match context
    """

    def __init__(self):
        """Initialize Poisson match predictor"""
        self.max_goals = 10  # Maximum goals to consider in calculations

    def calculate_lambda(self, team_attack: float, opponent_defense: float,
                        home_advantage: float = 1.3) -> float:
        """
        Calculate lambda (expected goals) for a team

        Args:
            team_attack: Team's attacking strength (e.g., avg goals scored)
            opponent_defense: Opponent's defensive weakness (e.g., avg goals conceded)
            home_advantage: Multiplier for home team (default 1.3 = 30% boost)

        Returns:
            Lambda parameter for Poisson distribution
        """
        return team_attack * opponent_defense * home_advantage

    def poisson_probability(self, lambda_param: float, k: int) -> float:
        """
        Calculate probability of scoring exactly k goals

        Args:
            lambda_param: Expected number of goals
            k: Number of goals

        Returns:
            Probability of scoring k goals
        """
        return poisson.pmf(k, lambda_param)

    def predict_match_simple(self, home_lambda: float, away_lambda: float) -> Dict:
        """
        Predict match outcome using simple Poisson model

        Args:
            home_lambda: Expected goals for home team
            away_lambda: Expected goals for away team

        Returns:
            Dictionary with probabilities and expected goals
        """
        # Calculate all possible score combinations up to max_goals
        probabilities = np.zeros((self.max_goals + 1, self.max_goals + 1))

        for home_goals in range(self.max_goals + 1):
            for away_goals in range(self.max_goals + 1):
                prob_home = self.poisson_probability(home_lambda, home_goals)
                prob_away = self.poisson_probability(away_lambda, away_goals)
                probabilities[home_goals, away_goals] = prob_home * prob_away

        # Calculate match outcome probabilities
        home_win_prob = np.sum(np.tril(probabilities, -1))  # Home goals > Away goals
        draw_prob = np.sum(np.diag(probabilities))  # Home goals = Away goals
        away_win_prob = np.sum(np.triu(probabilities, 1))  # Away goals > Home goals

        # Find most likely score
        most_likely_idx = np.unravel_index(probabilities.argmax(), probabilities.shape)
        most_likely_score = (most_likely_idx[0], most_likely_idx[1])
        most_likely_prob = probabilities[most_likely_idx]

        return {
            'home_lambda': home_lambda,
            'away_lambda': away_lambda,
            'home_win_prob': home_win_prob,
            'draw_prob': draw_prob,
            'away_win_prob': away_win_prob,
            'most_likely_score': most_likely_score,
            'most_likely_score_prob': most_likely_prob,
            'score_probabilities': probabilities
        }

    def simulate_match(self, home_lambda: float, away_lambda: float,
                      n_simulations: int = 10000) -> Dict:
        """
        Simulate match outcome using Monte Carlo simulation

        Args:
            home_lambda: Expected goals for home team
            away_lambda: Expected goals for away team
            n_simulations: Number of simulations to run

        Returns:
            Dictionary with simulation results
        """
        # Generate random goals for both teams
        home_goals = np.random.poisson(home_lambda, n_simulations)
        away_goals = np.random.poisson(away_lambda, n_simulations)

        # Calculate outcomes
        home_wins = np.sum(home_goals > away_goals)
        draws = np.sum(home_goals == away_goals)
        away_wins = np.sum(home_goals < away_goals)

        # Calculate probabilities
        home_win_prob = home_wins / n_simulations
        draw_prob = draws / n_simulations
        away_win_prob = away_wins / n_simulations

        # Average goals
        avg_home_goals = np.mean(home_goals)
        avg_away_goals = np.mean(away_goals)

        # Score distribution
        scores = list(zip(home_goals, away_goals))
        score_counts = pd.Series(scores).value_counts()
        most_common_score = score_counts.index[0]

        return {
            'home_lambda': home_lambda,
            'away_lambda': away_lambda,
            'n_simulations': n_simulations,
            'home_win_prob': home_win_prob,
            'draw_prob': draw_prob,
            'away_win_prob': away_win_prob,
            'avg_home_goals': avg_home_goals,
            'avg_away_goals': avg_away_goals,
            'most_common_score': most_common_score,
            'home_goals_std': np.std(home_goals),
            'away_goals_std': np.std(away_goals)
        }

    def predict_with_xg(self, home_xg: float, away_xg: float,
                       home_advantage: float = 0.3) -> Dict:
        """
        Predict match using xG (Expected Goals) values

        Args:
            home_xg: Expected goals for home team
            away_xg: Expected goals for away team
            home_advantage: Additional xG boost for home team

        Returns:
            Dictionary with prediction
        """
        # Add home advantage
        home_lambda = home_xg + home_advantage
        away_lambda = away_xg

        return self.predict_match_simple(home_lambda, away_lambda)

    def get_score_probabilities(self, home_lambda: float, away_lambda: float,
                               top_n: int = 10) -> pd.DataFrame:
        """
        Get most probable scores

        Args:
            home_lambda: Expected goals for home team
            away_lambda: Expected goals for away team
            top_n: Number of top scores to return

        Returns:
            DataFrame with most probable scores
        """
        scores = []

        for home_goals in range(self.max_goals + 1):
            for away_goals in range(self.max_goals + 1):
                prob_home = self.poisson_probability(home_lambda, home_goals)
                prob_away = self.poisson_probability(away_lambda, away_goals)
                combined_prob = prob_home * prob_away

                scores.append({
                    'HomeGoals': home_goals,
                    'AwayGoals': away_goals,
                    'Score': f"{home_goals}:{away_goals}",
                    'Probability': combined_prob
                })

        df = pd.DataFrame(scores)
        df = df.sort_values('Probability', ascending=False).head(top_n)
        df.reset_index(drop=True, inplace=True)

        return df

    def calculate_over_under(self, home_lambda: float, away_lambda: float,
                            threshold: float = 2.5) -> Dict:
        """
        Calculate over/under probabilities

        Args:
            home_lambda: Expected goals for home team
            away_lambda: Expected goals for away team
            threshold: Goal threshold (e.g., 2.5 for over/under 2.5 goals)

        Returns:
            Dictionary with over/under probabilities
        """
        total_lambda = home_lambda + away_lambda

        # Calculate probability of different total goals
        over_prob = 0
        under_prob = 0

        for total_goals in range(self.max_goals * 2 + 1):
            # Probability of exactly this many total goals
            # This is complex for sum of two Poisson distributions
            # We'll use simulation for accuracy
            pass

        # Simplified calculation using total lambda
        over_prob = 1 - poisson.cdf(int(threshold), total_lambda)
        under_prob = poisson.cdf(int(threshold), total_lambda)

        return {
            'threshold': threshold,
            'total_lambda': total_lambda,
            'over_prob': over_prob,
            'under_prob': under_prob
        }

    def calculate_btts(self, home_lambda: float, away_lambda: float) -> Dict:
        """
        Calculate Both Teams To Score (BTTS) probability

        Args:
            home_lambda: Expected goals for home team
            away_lambda: Expected goals for away team

        Returns:
            Dictionary with BTTS probabilities
        """
        # Probability home scores 0
        home_zero_prob = self.poisson_probability(home_lambda, 0)

        # Probability away scores 0
        away_zero_prob = self.poisson_probability(away_lambda, 0)

        # BTTS = both score at least 1
        btts_yes = (1 - home_zero_prob) * (1 - away_zero_prob)
        btts_no = 1 - btts_yes

        return {
            'btts_yes_prob': btts_yes,
            'btts_no_prob': btts_no,
            'home_zero_prob': home_zero_prob,
            'away_zero_prob': away_zero_prob
        }


def main():
    """Test Poisson match predictor"""

    print("=" * 70)
    print("Poisson Match Prediction Model - Test")
    print("=" * 70)

    predictor = PoissonMatchPredictor()

    # Test 1: Simple prediction
    print("\n1. Simple Poisson Prediction (Bayern vs Dortmund):")
    print("-" * 70)
    print("Assuming Bayern xG = 2.2, Dortmund xG = 1.5")

    prediction = predictor.predict_match_simple(
        home_lambda=2.2 + 0.3,  # Bayern with home advantage
        away_lambda=1.5
    )

    print(f"\nMatch Outcome Probabilities:")
    print(f"  Home Win: {prediction['home_win_prob']:.1%}")
    print(f"  Draw:     {prediction['draw_prob']:.1%}")
    print(f"  Away Win: {prediction['away_win_prob']:.1%}")
    print(f"\nMost Likely Score: {prediction['most_likely_score'][0]}:{prediction['most_likely_score'][1]}")
    print(f"Probability: {prediction['most_likely_score_prob']:.1%}")

    # Test 2: Monte Carlo simulation
    print("\n\n2. Monte Carlo Simulation (10,000 matches):")
    print("-" * 70)

    simulation = predictor.simulate_match(
        home_lambda=2.5,
        away_lambda=1.5,
        n_simulations=10000
    )

    print(f"Simulated Outcome Probabilities:")
    print(f"  Home Win: {simulation['home_win_prob']:.1%}")
    print(f"  Draw:     {simulation['draw_prob']:.1%}")
    print(f"  Away Win: {simulation['away_win_prob']:.1%}")
    print(f"\nAverage Goals:")
    print(f"  Home: {simulation['avg_home_goals']:.2f} (±{simulation['home_goals_std']:.2f})")
    print(f"  Away: {simulation['avg_away_goals']:.2f} (±{simulation['away_goals_std']:.2f})")
    print(f"\nMost Common Score: {simulation['most_common_score'][0]}:{simulation['most_common_score'][1]}")

    # Test 3: Score probabilities
    print("\n\n3. Most Probable Scores:")
    print("-" * 70)

    scores = predictor.get_score_probabilities(2.5, 1.5, top_n=10)
    scores['Probability_Pct'] = scores['Probability'] * 100
    print(scores[['Score', 'Probability_Pct']].to_string(index=False))

    # Test 4: Over/Under
    print("\n\n4. Over/Under 2.5 Goals:")
    print("-" * 70)

    ou = predictor.calculate_over_under(2.5, 1.5, threshold=2.5)
    print(f"Total Expected Goals: {ou['total_lambda']:.2f}")
    print(f"Over 2.5: {ou['over_prob']:.1%}")
    print(f"Under 2.5: {ou['under_prob']:.1%}")

    # Test 5: BTTS
    print("\n\n5. Both Teams To Score (BTTS):")
    print("-" * 70)

    btts = predictor.calculate_btts(2.5, 1.5)
    print(f"BTTS Yes: {btts['btts_yes_prob']:.1%}")
    print(f"BTTS No:  {btts['btts_no_prob']:.1%}")

    print("\n" + "=" * 70)
    print("Poisson Model Test Completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
