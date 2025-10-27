"""
Betting Odds Integration
Fetches and processes betting odds from various sources

Sources:
- The Odds API (https://the-odds-api.com/)
- Fallback: Web scraping from Oddsportal or similar

Converts odds to:
- Implied probabilities
- Expected goals (lambda for Poisson)
"""

import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import re

try:
    from .cache import get_cache
except ImportError:
    from cache import get_cache

# Cache configuration
CACHE_EXPIRY_HOURS = 6  # Odds change frequently, cache for 6 hours

# The Odds API configuration
# Get free API key at: https://the-odds-api.com/
ODDS_API_KEY = None  # User should set this via environment variable
ODDS_API_BASE_URL = "https://api.the-odds-api.com/v4"


class BettingOddsProvider:
    """
    Fetches betting odds from various providers
    Focuses on Bundesliga (German Football)
    """

    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True,
                 cache_expiry_hours: int = CACHE_EXPIRY_HOURS):
        """
        Initialize odds provider

        Args:
            api_key: API key for The Odds API (optional)
            use_cache: If True, use file cache to reduce API calls
            cache_expiry_hours: Hours until cached data expires
        """
        self.api_key = api_key or ODDS_API_KEY
        self.use_cache = use_cache
        self.cache_expiry_hours = cache_expiry_hours
        self.cache = get_cache(expiry_hours=cache_expiry_hours) if use_cache else None

        # For demo/testing: mock odds data
        self.mock_mode = not self.api_key

    def _normalize_team_name(self, team_name: str) -> str:
        """
        Normalize team name for matching

        Args:
            team_name: Team name from any source

        Returns:
            Normalized team name
        """
        # Remove common prefixes/suffixes
        replacements = {
            'FC Bayern München': 'Bayern München',
            'FC Bayern Munchen': 'Bayern München',
            'Bayern Munich': 'Bayern München',
            'Bayer 04 Leverkusen': 'Bayer Leverkusen',
            'RasenBallsport Leipzig': 'RB Leipzig',
            '1. FC Union Berlin': 'Union Berlin',
            'Sport-Club Freiburg': 'SC Freiburg',
            '1. FSV Mainz 05': 'Mainz 05',
            "Borussia M'gladbach": 'Borussia Mönchengladbach',
            '1. FC Köln': 'FC Köln',
            'TSG 1899 Hoffenheim': 'TSG Hoffenheim',
            'SV Werder Bremen': 'Werder Bremen',
            'VfL Bochum 1848': 'VfL Bochum',
            '1. FC Heidenheim 1846': 'FC Heidenheim',
        }

        normalized = team_name
        for old, new in replacements.items():
            if old.lower() in team_name.lower():
                normalized = new
                break

        return normalized

    def _remove_margin(self, probs: List[float], method: str = 'proportional') -> List[float]:
        """
        Remove bookmaker margin from probabilities

        Args:
            probs: List of implied probabilities (sum > 1.0 due to margin)
            method: 'proportional' or 'shin' (Shin's method)

        Returns:
            Fair probabilities (sum = 1.0)
        """
        if method == 'proportional':
            # Simple proportional method
            total = sum(probs)
            if total <= 0:
                return probs
            return [p / total for p in probs]

        elif method == 'shin':
            # Shin's method (more sophisticated)
            # For now, use proportional as fallback
            # TODO: Implement Shin's algorithm
            return self._remove_margin(probs, method='proportional')

        return probs

    def _odds_to_probability(self, odds: float, odds_format: str = 'decimal') -> float:
        """
        Convert odds to implied probability

        Args:
            odds: Odds value
            odds_format: 'decimal', 'american', or 'fractional'

        Returns:
            Implied probability (0-1)
        """
        if odds_format == 'decimal':
            # Decimal odds (European): 2.5 means 1/2.5 = 40%
            if odds <= 0:
                return 0.0
            return 1.0 / odds

        elif odds_format == 'american':
            # American odds: +150 or -200
            if odds >= 0:
                return 100 / (odds + 100)
            else:
                return abs(odds) / (abs(odds) + 100)

        elif odds_format == 'fractional':
            # Fractional odds: 3/1 means 1/(3+1) = 25%
            # odds should be provided as decimal (3.0 for 3/1)
            return 1.0 / (odds + 1)

        return 0.0

    def _probability_to_lambda(self, home_prob: float, draw_prob: float,
                              away_prob: float) -> Tuple[float, float]:
        """
        Convert match outcome probabilities to Poisson lambdas (expected goals)

        Uses empirical relationship between win probabilities and expected goals

        Args:
            home_prob: Probability of home win
            draw_prob: Probability of draw
            away_prob: Probability of away win

        Returns:
            Tuple of (home_lambda, away_lambda)
        """
        # Based on Bundesliga statistics and Poisson distribution
        # This is an approximation using empirical formulas

        # Average Bundesliga goals
        avg_total = 3.1
        avg_home = 1.7
        avg_away = 1.4

        # Estimate lambdas from probabilities
        # Strong home favorite → high home_lambda, low away_lambda
        # Balanced match → both around average

        # Win probability differential
        home_advantage = home_prob - away_prob

        # Map probability to lambda adjustment
        # home_advantage: -0.5 to +0.5 typically
        home_lambda = avg_home + (home_advantage * 1.2)
        away_lambda = avg_away - (home_advantage * 1.2)

        # Adjust based on draw probability
        # High draw prob → both lambdas closer to each other
        if draw_prob > 0.25:
            # Compress the difference
            mean_lambda = (home_lambda + away_lambda) / 2
            home_lambda = mean_lambda + (home_lambda - mean_lambda) * 0.7
            away_lambda = mean_lambda + (away_lambda - mean_lambda) * 0.7

        # Apply bounds
        home_lambda = max(0.5, min(3.5, home_lambda))
        away_lambda = max(0.5, min(3.0, away_lambda))

        return home_lambda, away_lambda

    def get_match_odds(self, home_team: str, away_team: str) -> Optional[Dict]:
        """
        Get betting odds for a specific match

        Args:
            home_team: Home team name
            away_team: Away team name

        Returns:
            Dictionary with odds data or None
        """
        # Normalize team names
        home_normalized = self._normalize_team_name(home_team)
        away_normalized = self._normalize_team_name(away_team)

        # Check cache first
        if self.use_cache and self.cache:
            cache_key = f"odds_{home_normalized}_{away_normalized}"
            cached_data = self.cache.get(cache_key, expiry_hours=self.cache_expiry_hours)
            if cached_data is not None:
                print(f"✓ Using cached odds for {home_team} vs {away_team}")
                return cached_data

        # In mock mode, generate realistic odds
        if self.mock_mode:
            print(f"⚠️  No Odds API key - using mock odds for {home_team} vs {away_team}")
            return self._generate_mock_odds(home_normalized, away_normalized)

        # TODO: Implement actual API call to The Odds API
        # For now, use mock data
        return self._generate_mock_odds(home_normalized, away_normalized)

    def _generate_mock_odds(self, home_team: str, away_team: str) -> Dict:
        """
        Generate mock odds for testing (when no API key available)

        Args:
            home_team: Home team name
            away_team: Away team name

        Returns:
            Dictionary with mock odds
        """
        # Simple mock based on team names
        # Top teams: Bayern, Dortmund, Leverkusen, Leipzig
        top_teams = ['Bayern München', 'Borussia Dortmund', 'Bayer Leverkusen', 'RB Leipzig']
        mid_teams = ['VfB Stuttgart', 'Eintracht Frankfurt', 'VfL Wolfsburg', 'SC Freiburg']

        # Determine odds based on rough team strength
        if home_team in top_teams and away_team not in top_teams + mid_teams:
            # Strong home team vs weak away
            odds = {'home': 1.5, 'draw': 4.5, 'away': 7.0}
        elif away_team in top_teams and home_team not in top_teams + mid_teams:
            # Weak home team vs strong away
            odds = {'home': 6.0, 'draw': 4.5, 'away': 1.6}
        elif home_team in top_teams and away_team in top_teams:
            # Top vs top (with home advantage)
            odds = {'home': 2.2, 'draw': 3.5, 'away': 3.0}
        else:
            # Balanced match
            odds = {'home': 2.5, 'draw': 3.4, 'away': 2.8}

        # Convert to probabilities
        home_prob = self._odds_to_probability(odds['home'])
        draw_prob = self._odds_to_probability(odds['draw'])
        away_prob = self._odds_to_probability(odds['away'])

        # Remove margin
        fair_probs = self._remove_margin([home_prob, draw_prob, away_prob])

        # Convert to lambdas
        home_lambda, away_lambda = self._probability_to_lambda(
            fair_probs[0], fair_probs[1], fair_probs[2]
        )

        result = {
            'home_team': home_team,
            'away_team': away_team,
            'odds_decimal': odds,
            'implied_probabilities': {
                'home': home_prob,
                'draw': draw_prob,
                'away': away_prob
            },
            'fair_probabilities': {
                'home': fair_probs[0],
                'draw': fair_probs[1],
                'away': fair_probs[2]
            },
            'expected_goals': {
                'home': home_lambda,
                'away': away_lambda
            },
            'margin': (home_prob + draw_prob + away_prob - 1.0),
            'source': 'mock',
            'timestamp': datetime.now().isoformat()
        }

        # Cache the result
        if self.use_cache and self.cache:
            cache_key = f"odds_{home_team}_{away_team}"
            self.cache.set(cache_key, result)

        return result


def get_odds_strength(home_team: str, away_team: str) -> Tuple[float, float]:
    """
    Get normalized odds strength for prediction engine

    Args:
        home_team: Home team name
        away_team: Away team name

    Returns:
        Tuple of (home_strength, away_strength) normalized to 0-1
    """
    provider = BettingOddsProvider()
    odds_data = provider.get_match_odds(home_team, away_team)

    if not odds_data:
        return 0.5, 0.5

    fair_probs = odds_data['fair_probabilities']

    # Normalize to 0-1 scale (excluding draw)
    home_prob = fair_probs['home']
    away_prob = fair_probs['away']
    total = home_prob + away_prob

    if total <= 0:
        return 0.5, 0.5

    return home_prob / total, away_prob / total


def get_odds_lambdas(home_team: str, away_team: str) -> Tuple[float, float]:
    """
    Get expected goals (lambdas) from betting odds

    Args:
        home_team: Home team name
        away_team: Away team name

    Returns:
        Tuple of (home_lambda, away_lambda)
    """
    provider = BettingOddsProvider()
    odds_data = provider.get_match_odds(home_team, away_team)

    if not odds_data:
        return 1.7, 1.4  # Bundesliga averages

    return odds_data['expected_goals']['home'], odds_data['expected_goals']['away']


def main():
    """Test betting odds module"""

    print("=" * 80)
    print("Betting Odds Integration - Test")
    print("=" * 80)

    provider = BettingOddsProvider()

    # Test matches
    test_matches = [
        ("Bayern München", "VfL Bochum"),
        ("VfB Stuttgart", "RB Leipzig"),
        ("SC Freiburg", "Werder Bremen")
    ]

    for home, away in test_matches:
        print(f"\n{'='*80}")
        print(f"Match: {home} vs {away}")
        print('-' * 80)

        odds_data = provider.get_match_odds(home, away)

        if odds_data:
            print(f"\n📊 Decimal Odds:")
            print(f"  Home: {odds_data['odds_decimal']['home']:.2f}")
            print(f"  Draw: {odds_data['odds_decimal']['draw']:.2f}")
            print(f"  Away: {odds_data['odds_decimal']['away']:.2f}")

            print(f"\n📈 Implied Probabilities (with margin):")
            print(f"  Home: {odds_data['implied_probabilities']['home']:.1%}")
            print(f"  Draw: {odds_data['implied_probabilities']['draw']:.1%}")
            print(f"  Away: {odds_data['implied_probabilities']['away']:.1%}")
            print(f"  Margin: {odds_data['margin']:.1%}")

            print(f"\n✨ Fair Probabilities (margin removed):")
            print(f"  Home: {odds_data['fair_probabilities']['home']:.1%}")
            print(f"  Draw: {odds_data['fair_probabilities']['draw']:.1%}")
            print(f"  Away: {odds_data['fair_probabilities']['away']:.1%}")

            print(f"\n⚽ Expected Goals (from odds):")
            print(f"  Home: {odds_data['expected_goals']['home']:.2f}")
            print(f"  Away: {odds_data['expected_goals']['away']:.2f}")

            print(f"\n🔗 Source: {odds_data['source']}")

    print("\n" + "=" * 80)
    print("Betting Odds Test Completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
