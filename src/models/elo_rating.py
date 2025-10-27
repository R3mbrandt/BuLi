"""
ELO Rating System for Bundesliga Teams
Calculates and updates ELO ratings based on match results
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from datetime import datetime

try:
    from ..data_sources.cache import get_cache
except ImportError:
    try:
        from data_sources.cache import get_cache
    except ImportError:
        from cache import get_cache

# Cache configuration
CACHE_EXPIRY_HOURS = 24  # Cache ELO ratings for 24 hours


class ELORatingSystem:
    """
    ELO Rating System for football teams

    Based on the standard ELO formula with adjustments for football:
    - Home advantage factor
    - Goal difference consideration
    - K-factor adjustments
    """

    def __init__(self, k_factor: float = 32, home_advantage: float = 100, base_elo: float = 1500,
                 use_cache: bool = True, cache_expiry_hours: int = CACHE_EXPIRY_HOURS):
        """
        Initialize ELO rating system

        Args:
            k_factor: K-factor for rating adjustments (higher = more volatile)
            home_advantage: ELO points advantage for home team
            base_elo: Starting ELO rating for new teams
            use_cache: If True, use file cache to speed up rating calculations
            cache_expiry_hours: Hours until cached data expires
        """
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.base_elo = base_elo
        self.ratings: Dict[str, float] = {}
        self.use_cache = use_cache
        self.cache_expiry_hours = cache_expiry_hours
        self.cache = get_cache(expiry_hours=cache_expiry_hours) if use_cache else None

    def get_rating(self, team: str) -> float:
        """
        Get current ELO rating for a team

        Args:
            team: Team name

        Returns:
            Current ELO rating
        """
        return self.ratings.get(team, self.base_elo)

    def expected_score(self, rating_a: float, rating_b: float) -> float:
        """
        Calculate expected score for team A against team B

        Args:
            rating_a: ELO rating of team A
            rating_b: ELO rating of team B

        Returns:
            Expected score (probability of winning) for team A
        """
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))

    def get_actual_score(self, goals_for: int, goals_against: int) -> float:
        """
        Convert match result to actual score

        Args:
            goals_for: Goals scored by the team
            goals_against: Goals conceded by the team

        Returns:
            Actual score (1.0 for win, 0.5 for draw, 0.0 for loss)
        """
        if goals_for > goals_against:
            return 1.0
        elif goals_for == goals_against:
            return 0.5
        else:
            return 0.0

    def get_goal_difference_multiplier(self, goal_diff: int) -> float:
        """
        Calculate goal difference multiplier for ELO adjustment

        Larger victories are weighted more heavily

        Args:
            goal_diff: Absolute goal difference

        Returns:
            Multiplier for ELO change
        """
        if goal_diff <= 1:
            return 1.0
        elif goal_diff == 2:
            return 1.5
        else:
            return (11 + abs(goal_diff)) / 8

    def update_rating(self, team: str, opponent: str,
                     goals_for: int, goals_against: int,
                     is_home: bool = True) -> Tuple[float, float]:
        """
        Update ELO rating after a match

        Args:
            team: Team name
            opponent: Opponent name
            goals_for: Goals scored by team
            goals_against: Goals scored by opponent
            is_home: Whether team played at home

        Returns:
            Tuple of (old_rating, new_rating)
        """
        # Get current ratings
        team_rating = self.get_rating(team)
        opponent_rating = self.get_rating(opponent)

        # Apply home advantage
        if is_home:
            team_rating_adjusted = team_rating + self.home_advantage
        else:
            team_rating_adjusted = team_rating

        # Calculate expected score
        expected = self.expected_score(team_rating_adjusted, opponent_rating)

        # Get actual score
        actual = self.get_actual_score(goals_for, goals_against)

        # Calculate goal difference multiplier
        goal_diff = abs(goals_for - goals_against)
        gd_multiplier = self.get_goal_difference_multiplier(goal_diff)

        # Calculate rating change
        rating_change = self.k_factor * gd_multiplier * (actual - expected)

        # Update rating
        new_rating = team_rating + rating_change
        self.ratings[team] = new_rating

        return team_rating, new_rating

    def process_match(self, home_team: str, away_team: str,
                     home_goals: int, away_goals: int) -> Dict:
        """
        Process a match and update both teams' ratings

        Args:
            home_team: Home team name
            away_team: Away team name
            home_goals: Goals scored by home team
            away_goals: Goals scored by away team

        Returns:
            Dictionary with rating changes
        """
        # Update home team
        home_old, home_new = self.update_rating(
            home_team, away_team, home_goals, away_goals, is_home=True
        )

        # Update away team
        away_old, away_new = self.update_rating(
            away_team, home_team, away_goals, home_goals, is_home=False
        )

        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_goals': home_goals,
            'away_goals': away_goals,
            'home_elo_old': home_old,
            'home_elo_new': home_new,
            'home_elo_change': home_new - home_old,
            'away_elo_old': away_old,
            'away_elo_new': away_new,
            'away_elo_change': away_new - away_old
        }

    def save_ratings_to_cache(self, cache_key: str = "elo_ratings_bundesliga") -> bool:
        """
        Save current ELO ratings to cache

        Args:
            cache_key: Key to use for caching

        Returns:
            True if saved successfully, False otherwise
        """
        if not self.use_cache or not self.cache:
            return False

        try:
            self.cache.set(cache_key, self.ratings)
            print(f"✓ Saved ELO ratings to cache ({len(self.ratings)} teams)")
            return True
        except Exception as e:
            print(f"⚠️  Failed to save ELO ratings to cache: {e}")
            return False

    def load_ratings_from_cache(self, cache_key: str = "elo_ratings_bundesliga") -> bool:
        """
        Load ELO ratings from cache

        Args:
            cache_key: Key to use for caching

        Returns:
            True if loaded successfully, False otherwise
        """
        if not self.use_cache or not self.cache:
            return False

        try:
            cached_ratings = self.cache.get(cache_key, expiry_hours=self.cache_expiry_hours)
            if cached_ratings is not None:
                self.ratings = cached_ratings
                print(f"✓ Loaded ELO ratings from cache ({len(self.ratings)} teams)")
                return True
            return False
        except Exception as e:
            print(f"⚠️  Failed to load ELO ratings from cache: {e}")
            return False

    def process_matches_from_dataframe(self, matches_df: pd.DataFrame,
                                      initial_ratings: Optional[Dict[str, float]] = None,
                                      cache_key: str = "elo_ratings_bundesliga") -> pd.DataFrame:
        """
        Process multiple matches from a DataFrame and track ELO progression (with caching)

        Args:
            matches_df: DataFrame with columns: HomeTeam, AwayTeam, HomeGoals, AwayGoals
            initial_ratings: Optional dict of initial team ratings
            cache_key: Key for caching the final ratings

        Returns:
            DataFrame with ELO changes for each match
        """
        # Try to load from cache first
        if self.use_cache and not initial_ratings:
            if self.load_ratings_from_cache(cache_key):
                # Check if cached ratings are still valid by comparing with matches
                # For now, we'll just use the cached ratings
                pass

        if initial_ratings:
            self.ratings = initial_ratings.copy()

        results = []

        for _, match in matches_df.iterrows():
            result = self.process_match(
                match['HomeTeam'],
                match['AwayTeam'],
                match['HomeGoals'],
                match['AwayGoals']
            )
            results.append(result)

        # Save ratings to cache after processing
        if self.use_cache:
            self.save_ratings_to_cache(cache_key)

        return pd.DataFrame(results)

    def get_all_ratings(self) -> pd.DataFrame:
        """
        Get current ratings for all teams

        Returns:
            DataFrame with team ratings sorted by ELO
        """
        ratings_list = [
            {'Team': team, 'ELO': rating}
            for team, rating in self.ratings.items()
        ]

        df = pd.DataFrame(ratings_list)
        df = df.sort_values('ELO', ascending=False)
        df.reset_index(drop=True, inplace=True)
        df.insert(0, 'Rank', range(1, len(df) + 1))

        return df

    def predict_match(self, home_team: str, away_team: str) -> Dict:
        """
        Predict match outcome based on current ELO ratings

        Args:
            home_team: Home team name
            away_team: Away team name

        Returns:
            Dictionary with prediction details
        """
        home_rating = self.get_rating(home_team)
        away_rating = self.get_rating(away_team)

        # Apply home advantage
        home_rating_adjusted = home_rating + self.home_advantage

        # Calculate win probabilities
        home_win_prob = self.expected_score(home_rating_adjusted, away_rating)
        away_win_prob = self.expected_score(away_rating, home_rating_adjusted)

        # Draw probability (simplified)
        # In reality, this would be calculated differently
        draw_prob = 1 - home_win_prob - away_win_prob
        if draw_prob < 0:
            draw_prob = 0.25  # Default draw probability

        # Normalize probabilities
        total = home_win_prob + draw_prob + away_win_prob
        home_win_prob /= total
        draw_prob /= total
        away_win_prob /= total

        return {
            'home_team': home_team,
            'away_team': away_team,
            'home_elo': home_rating,
            'away_elo': away_rating,
            'home_win_prob': home_win_prob,
            'draw_prob': draw_prob,
            'away_win_prob': away_win_prob,
            'elo_difference': home_rating - away_rating
        }


def main():
    """Test ELO rating system"""

    print("=" * 70)
    print("ELO Rating System - Test")
    print("=" * 70)

    # Import mock data
    import sys
    sys.path.append('/home/user/BuLi/src')
    from data_sources.mock_data import generate_mock_matches, BUNDESLIGA_TEAMS

    # Initialize ELO system
    elo = ELORatingSystem(k_factor=32, home_advantage=100)

    # Set initial ratings from mock data
    initial_ratings = {team: data['base_elo'] for team, data in BUNDESLIGA_TEAMS.items()}
    elo.ratings = initial_ratings.copy()

    print("\n1. Initial ELO Ratings:")
    print("-" * 70)
    initial_df = elo.get_all_ratings()
    print(initial_df.head(10).to_string(index=False))

    # Generate and process matches
    print("\n\n2. Processing Matches:")
    print("-" * 70)
    matches = generate_mock_matches(10)
    print(f"Processing {len(matches)} matches...")

    match_results = elo.process_matches_from_dataframe(matches, initial_ratings)

    print("\nSample match results with ELO changes:")
    display_cols = ['home_team', 'away_team', 'home_goals', 'away_goals',
                   'home_elo_change', 'away_elo_change']
    print(match_results.head(10)[display_cols].to_string(index=False))

    # Show updated ratings
    print("\n\n3. Updated ELO Ratings After Matches:")
    print("-" * 70)
    updated_df = elo.get_all_ratings()
    print(updated_df.head(10).to_string(index=False))

    # Test prediction
    print("\n\n4. Match Prediction (Bayern vs Dortmund):")
    print("-" * 70)
    prediction = elo.predict_match('Bayern München', 'Borussia Dortmund')

    print(f"{prediction['home_team']:30s} ELO: {prediction['home_elo']:.1f}")
    print(f"{prediction['away_team']:30s} ELO: {prediction['away_elo']:.1f}")
    print(f"\nELO Difference: {prediction['elo_difference']:+.1f}")
    print(f"\nProbabilities:")
    print(f"  Home Win: {prediction['home_win_prob']:.1%}")
    print(f"  Draw:     {prediction['draw_prob']:.1%}")
    print(f"  Away Win: {prediction['away_win_prob']:.1%}")

    print("\n" + "=" * 70)
    print("ELO Rating System Test Completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
