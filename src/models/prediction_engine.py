"""
Bundesliga Match Prediction Engine
Combines multiple data sources and models to predict match outcomes:
- ELO ratings
- xG (Expected Goals)
- Squad value (monetary)
- Injuries
- Head-to-head record
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple
from datetime import datetime

try:
    from .elo_rating import ELORatingSystem
    from .poisson_model import PoissonMatchPredictor
except ImportError:
    # For standalone execution
    from elo_rating import ELORatingSystem
    from poisson_model import PoissonMatchPredictor


class BundesligaPredictionEngine:
    """
    Main prediction engine that combines all factors
    """

    def __init__(self):
        """Initialize prediction engine"""
        self.elo_system = ELORatingSystem(k_factor=32, home_advantage=100)
        self.poisson_predictor = PoissonMatchPredictor()

        # Weights for different factors (must sum to 1.0)
        self.weights = {
            'elo': 0.35,          # ELO ratings
            'xg': 0.30,           # Expected goals
            'squad_value': 0.15,  # Monetary squad value
            'injuries': 0.10,     # Injury impact
            'h2h': 0.10           # Head-to-head record
        }

    def set_weights(self, elo: float = 0.35, xg: float = 0.30,
                   squad_value: float = 0.15, injuries: float = 0.10,
                   h2h: float = 0.10):
        """
        Set custom weights for prediction factors

        Args:
            elo: Weight for ELO ratings
            xg: Weight for xG data
            squad_value: Weight for squad value
            injuries: Weight for injuries
            h2h: Weight for head-to-head
        """
        total = elo + xg + squad_value + injuries + h2h
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

        self.weights = {
            'elo': elo,
            'xg': xg,
            'squad_value': squad_value,
            'injuries': injuries,
            'h2h': h2h
        }

    def calculate_elo_strength(self, home_elo: float, away_elo: float) -> Tuple[float, float]:
        """
        Convert ELO ratings to attacking/defensive strengths

        Args:
            home_elo: Home team ELO
            away_elo: Away team ELO

        Returns:
            Tuple of (home_strength, away_strength) normalized to 0-1 scale
        """
        # Normalize ELO difference to 0-1 scale
        # Higher ELO = higher strength
        elo_diff = home_elo - away_elo
        home_strength = 1 / (1 + 10 ** (-elo_diff / 400))
        away_strength = 1 - home_strength

        return home_strength, away_strength

    def calculate_xg_strength(self, home_xg_for: float, home_xg_against: float,
                             away_xg_for: float, away_xg_against: float) -> Tuple[float, float]:
        """
        Calculate team strengths based on xG data

        Args:
            home_xg_for: Home team's average xG for
            home_xg_against: Home team's average xG against
            away_xg_for: Away team's average xG for
            away_xg_against: Away team's average xG against

        Returns:
            Tuple of (home_strength, away_strength)
        """
        # Home team: strong attack + weak defense of opponent
        home_attack = home_xg_for
        away_defense = away_xg_against

        # Away team: strong attack + weak defense of opponent
        away_attack = away_xg_for
        home_defense = home_xg_against

        # Combine attack and defense
        home_strength = (home_attack + away_defense) / 2
        away_strength = (away_attack + home_defense) / 2

        # Normalize
        total = home_strength + away_strength
        if total > 0:
            home_strength /= total
            away_strength /= total

        return home_strength, away_strength

    def calculate_value_strength(self, home_value: float, away_value: float) -> Tuple[float, float]:
        """
        Calculate team strengths based on squad monetary value

        Args:
            home_value: Home team squad value in EUR
            away_value: Away team squad value in EUR

        Returns:
            Tuple of (home_strength, away_strength)
        """
        total_value = home_value + away_value

        if total_value == 0:
            return 0.5, 0.5

        home_strength = home_value / total_value
        away_strength = away_value / total_value

        return home_strength, away_strength

    def calculate_injury_impact(self, home_injuries: int, away_injuries: int,
                               max_impact: float = 0.15) -> Tuple[float, float]:
        """
        Calculate impact of injuries on team strength

        Args:
            home_injuries: Number of injured players for home team
            away_injuries: Number of injured players for away team
            max_impact: Maximum impact of injuries (0-1)

        Returns:
            Tuple of (home_penalty, away_penalty) where 0 = no impact, 1 = max impact
        """
        # Fewer injuries = lower penalty
        # Each injury reduces strength by a certain amount
        injury_penalty_per_player = max_impact / 5  # Assume 5 injuries = max impact

        home_penalty = min(home_injuries * injury_penalty_per_player, max_impact)
        away_penalty = min(away_injuries * injury_penalty_per_player, max_impact)

        return home_penalty, away_penalty

    def calculate_h2h_strength(self, h2h_data: pd.DataFrame, home_team: str,
                              away_team: str) -> Tuple[float, float]:
        """
        Calculate strengths based on head-to-head record

        Args:
            h2h_data: DataFrame with H2H matches
            home_team: Home team name
            away_team: Away team name

        Returns:
            Tuple of (home_strength, away_strength)
        """
        if h2h_data.empty:
            return 0.5, 0.5

        # Count wins for each team
        home_wins = 0
        away_wins = 0
        draws = 0

        for _, match in h2h_data.iterrows():
            if match['HomeTeam'] == home_team:
                if match['HomeGoals'] > match['AwayGoals']:
                    home_wins += 1
                elif match['HomeGoals'] < match['AwayGoals']:
                    away_wins += 1
                else:
                    draws += 1
            else:  # home_team was away
                if match['AwayGoals'] > match['HomeGoals']:
                    home_wins += 1
                elif match['AwayGoals'] < match['HomeGoals']:
                    away_wins += 1
                else:
                    draws += 1

        total_matches = len(h2h_data)
        if total_matches == 0:
            return 0.5, 0.5

        # Calculate strength (wins + 0.5*draws)
        home_points = home_wins + 0.5 * draws
        away_points = away_wins + 0.5 * draws

        total_points = home_points + away_points
        if total_points == 0:
            return 0.5, 0.5

        home_strength = home_points / total_points
        away_strength = away_points / total_points

        return home_strength, away_strength

    def predict_match(self, home_team: str, away_team: str,
                     home_data: Dict, away_data: Dict,
                     h2h_matches: Optional[pd.DataFrame] = None) -> Dict:
        """
        Predict match outcome using all available data

        Args:
            home_team: Home team name
            away_team: Away team name
            home_data: Dictionary with home team data (elo, xg_for, xg_against, value, injuries)
            away_data: Dictionary with away team data
            h2h_matches: DataFrame with head-to-head matches

        Returns:
            Dictionary with comprehensive prediction
        """
        # Calculate individual strengths
        elo_home, elo_away = self.calculate_elo_strength(
            home_data.get('elo', 1500),
            away_data.get('elo', 1500)
        )

        xg_home, xg_away = self.calculate_xg_strength(
            home_data.get('xg_for', 1.5),
            home_data.get('xg_against', 1.5),
            away_data.get('xg_for', 1.5),
            away_data.get('xg_against', 1.5)
        )

        value_home, value_away = self.calculate_value_strength(
            home_data.get('squad_value', 100_000_000),
            away_data.get('squad_value', 100_000_000)
        )

        injury_penalty_home, injury_penalty_away = self.calculate_injury_impact(
            home_data.get('injuries', 0),
            away_data.get('injuries', 0)
        )

        h2h_home, h2h_away = self.calculate_h2h_strength(
            h2h_matches if h2h_matches is not None else pd.DataFrame(),
            home_team,
            away_team
        )

        # Combine strengths using weights
        combined_home = (
            self.weights['elo'] * elo_home +
            self.weights['xg'] * xg_home +
            self.weights['squad_value'] * value_home +
            self.weights['h2h'] * h2h_home
        )

        combined_away = (
            self.weights['elo'] * elo_away +
            self.weights['xg'] * xg_away +
            self.weights['squad_value'] * value_away +
            self.weights['h2h'] * h2h_away
        )

        # Apply injury penalties
        combined_home *= (1 - injury_penalty_home)
        combined_away *= (1 - injury_penalty_away)

        # Normalize
        total = combined_home + combined_away
        if total > 0:
            combined_home /= total
            combined_away /= total

        # Convert to expected goals (lambda for Poisson)
        # Base expectation is 1.5 goals, scaled by strength
        base_goals = 1.5
        home_lambda = base_goals * (combined_home / combined_away) * 1.3  # Home advantage
        away_lambda = base_goals * (combined_away / combined_home)

        # Use Poisson model for final prediction
        poisson_pred = self.poisson_predictor.predict_match_simple(home_lambda, away_lambda)

        # Get most probable scores
        top_scores = self.poisson_predictor.get_score_probabilities(home_lambda, away_lambda, top_n=5)

        # Calculate betting metrics
        ou = self.poisson_predictor.calculate_over_under(home_lambda, away_lambda, threshold=2.5)
        btts = self.poisson_predictor.calculate_btts(home_lambda, away_lambda)

        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_win_prob': poisson_pred['home_win_prob'],
            'draw_prob': poisson_pred['draw_prob'],
            'away_win_prob': poisson_pred['away_win_prob'],
            'expected_home_goals': home_lambda,
            'expected_away_goals': away_lambda,
            'most_likely_score': f"{poisson_pred['most_likely_score'][0]}:{poisson_pred['most_likely_score'][1]}",
            'most_likely_score_prob': poisson_pred['most_likely_score_prob'],
            'top_scores': top_scores,
            'over_2_5_prob': ou['over_prob'],
            'under_2_5_prob': ou['under_prob'],
            'btts_yes_prob': btts['btts_yes_prob'],
            'btts_no_prob': btts['btts_no_prob'],
            'factor_strengths': {
                'elo': {'home': elo_home, 'away': elo_away},
                'xg': {'home': xg_home, 'away': xg_away},
                'squad_value': {'home': value_home, 'away': value_away},
                'h2h': {'home': h2h_home, 'away': h2h_away},
                'injury_penalty': {'home': injury_penalty_home, 'away': injury_penalty_away}
            },
            'combined_strength': {'home': combined_home, 'away': combined_away}
        }

    def format_prediction_report(self, prediction: Dict) -> str:
        """
        Format prediction as a readable report

        Args:
            prediction: Prediction dictionary from predict_match

        Returns:
            Formatted string report
        """
        report = []
        report.append("=" * 70)
        report.append(f"MATCH PREDICTION: {prediction['home_team']} vs {prediction['away_team']}")
        report.append("=" * 70)

        report.append("\n📊 MATCH OUTCOME PROBABILITIES:")
        report.append("-" * 70)
        report.append(f"  Home Win: {prediction['home_win_prob']:>6.1%}")
        report.append(f"  Draw:     {prediction['draw_prob']:>6.1%}")
        report.append(f"  Away Win: {prediction['away_win_prob']:>6.1%}")

        report.append("\n⚽ EXPECTED GOALS:")
        report.append("-" * 70)
        report.append(f"  {prediction['home_team']:30s}: {prediction['expected_home_goals']:.2f}")
        report.append(f"  {prediction['away_team']:30s}: {prediction['expected_away_goals']:.2f}")

        report.append("\n🎯 MOST LIKELY SCORE:")
        report.append("-" * 70)
        report.append(f"  {prediction['most_likely_score']} ({prediction['most_likely_score_prob']:.1%})")

        report.append("\n📈 TOP 5 PROBABLE SCORES:")
        report.append("-" * 70)
        for idx, row in prediction['top_scores'].iterrows():
            report.append(f"  {row['Score']:>5s} - {row['Probability']*100:>5.1f}%")

        report.append("\n💰 BETTING INSIGHTS:")
        report.append("-" * 70)
        report.append(f"  Over 2.5 Goals:  {prediction['over_2_5_prob']:.1%}")
        report.append(f"  Under 2.5 Goals: {prediction['under_2_5_prob']:.1%}")
        report.append(f"  BTTS Yes:        {prediction['btts_yes_prob']:.1%}")
        report.append(f"  BTTS No:         {prediction['btts_no_prob']:.1%}")

        report.append("\n🔍 FACTOR BREAKDOWN:")
        report.append("-" * 70)
        factors = prediction['factor_strengths']
        report.append(f"  ELO:         Home {factors['elo']['home']:.1%} | Away {factors['elo']['away']:.1%}")
        report.append(f"  xG:          Home {factors['xg']['home']:.1%} | Away {factors['xg']['away']:.1%}")
        report.append(f"  Squad Value: Home {factors['squad_value']['home']:.1%} | Away {factors['squad_value']['away']:.1%}")
        report.append(f"  H2H:         Home {factors['h2h']['home']:.1%} | Away {factors['h2h']['away']:.1%}")
        report.append(f"  Injuries:    Home -{factors['injury_penalty']['home']:.1%} | Away -{factors['injury_penalty']['away']:.1%}")

        combined = prediction['combined_strength']
        report.append(f"\n  Combined:    Home {combined['home']:.1%} | Away {combined['away']:.1%}")

        report.append("\n" + "=" * 70)

        return "\n".join(report)


def main():
    """Test prediction engine"""

    print("=" * 70)
    print("Bundesliga Prediction Engine - Test")
    print("=" * 70)

    engine = BundesligaPredictionEngine()

    # Example match: Bayern München vs Borussia Dortmund
    home_data = {
        'elo': 1900,
        'xg_for': 2.3,
        'xg_against': 1.1,
        'squad_value': 850_000_000,
        'injuries': 2
    }

    away_data = {
        'elo': 1820,
        'xg_for': 2.0,
        'xg_against': 1.3,
        'squad_value': 520_000_000,
        'injuries': 3
    }

    # Simulate H2H data
    h2h_data = pd.DataFrame([
        {'HomeTeam': 'Bayern München', 'AwayTeam': 'Borussia Dortmund', 'HomeGoals': 3, 'AwayGoals': 2},
        {'HomeTeam': 'Borussia Dortmund', 'AwayTeam': 'Bayern München', 'HomeGoals': 2, 'AwayGoals': 2},
        {'HomeTeam': 'Bayern München', 'AwayTeam': 'Borussia Dortmund', 'HomeGoals': 4, 'AwayGoals': 2},
        {'HomeTeam': 'Borussia Dortmund', 'AwayTeam': 'Bayern München', 'HomeGoals': 2, 'AwayGoals': 3},
        {'HomeTeam': 'Bayern München', 'AwayTeam': 'Borussia Dortmund', 'HomeGoals': 1, 'AwayGoals': 1},
    ])

    # Make prediction
    prediction = engine.predict_match(
        'Bayern München',
        'Borussia Dortmund',
        home_data,
        away_data,
        h2h_data
    )

    # Print formatted report
    report = engine.format_prediction_report(prediction)
    print(report)


if __name__ == "__main__":
    main()
