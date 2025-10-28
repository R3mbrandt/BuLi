"""
Betting Odds Integration (Powered by API-Football)
Fetches betting odds from professional bookmakers:
- Pinnacle (lowest margin, professional odds)
- Betfair Exchange (fair odds, no bookmaker margin)
- Bet365 (popular bookmaker, good coverage)

Provides:
- Decimal odds conversion to probabilities
- Margin removal (using Betfair as benchmark)
- Probability to Poisson lambda conversion
"""

from typing import Dict, Tuple, Optional

try:
    from .api_football import APIFootballClient
    from ..utils.season import get_current_season
except (ImportError, ValueError):
    # Handle both direct execution and package import issues
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from data_sources.api_football import APIFootballClient
    from utils.season import get_current_season


def _odds_to_probability(odds: float) -> float:
    """
    Convert decimal odds to implied probability

    Args:
        odds: Decimal odds (e.g., 2.5)

    Returns:
        Implied probability (0-1)
    """
    if odds <= 0:
        return 0.0
    return 1.0 / odds


def _remove_margin(probs: Dict[str, float], method: str = 'betfair') -> Dict[str, float]:
    """
    Remove bookmaker margin from probabilities

    Args:
        probs: Dictionary with 'home', 'draw', 'away' probabilities
        method: 'betfair' (use Betfair as fair) or 'proportional'

    Returns:
        Fair probabilities (sum = 1.0)
    """
    if method == 'betfair':
        # Betfair Exchange has no margin - already fair
        return probs

    # Proportional method
    total = probs['home'] + probs['draw'] + probs['away']
    if total <= 0:
        return probs

    return {
        'home': probs['home'] / total,
        'draw': probs['draw'] / total,
        'away': probs['away'] / total
    }


def _probability_to_lambda(home_prob: float, draw_prob: float, away_prob: float) -> Tuple[float, float]:
    """
    Convert match outcome probabilities to Poisson lambdas (expected goals)

    Args:
        home_prob: Probability of home win
        draw_prob: Probability of draw
        away_prob: Probability of away win

    Returns:
        Tuple of (home_lambda, away_lambda)
    """
    # Bundesliga averages
    avg_home = 1.7
    avg_away = 1.4

    # Win probability differential
    home_advantage = home_prob - away_prob

    # Map probability to lambda adjustment
    home_lambda = avg_home + (home_advantage * 1.2)
    away_lambda = avg_away - (home_advantage * 1.2)

    # Adjust based on draw probability
    # High draw prob → both lambdas closer to each other
    if draw_prob > 0.25:
        mean_lambda = (home_lambda + away_lambda) / 2
        home_lambda = mean_lambda + (home_lambda - mean_lambda) * 0.7
        away_lambda = mean_lambda + (away_lambda - mean_lambda) * 0.7

    # Apply bounds
    home_lambda = max(0.5, min(3.5, home_lambda))
    away_lambda = max(0.5, min(3.0, away_lambda))

    return home_lambda, away_lambda


def get_odds_strength(home_team: str, away_team: str, season: Optional[int] = None) -> Tuple[float, float]:
    """
    Get normalized odds strength for prediction engine

    Args:
        home_team: Home team name
        away_team: Away team name
        season: Season year (defaults to current season)

    Returns:
        Tuple of (home_strength, away_strength) normalized to 0-1
    """
    if season is None:
        season = get_current_season()

    client = APIFootballClient()
    odds_data = client.get_match_odds(home_team, away_team, season)

    if not odds_data:
        return 0.5, 0.5

    # Prefer Betfair (fair odds), fallback to Pinnacle, then Bet365
    odds = odds_data.get('fair_odds') or odds_data.get('pinnacle') or odds_data.get('bet365')

    if not odds:
        return 0.5, 0.5

    # Convert to probabilities
    home_prob = _odds_to_probability(odds.get('home', 0))
    draw_prob = _odds_to_probability(odds.get('draw', 0))
    away_prob = _odds_to_probability(odds.get('away', 0))

    # Remove margin (if not using Betfair)
    if odds == odds_data.get('fair_odds'):
        fair_probs = {'home': home_prob, 'draw': draw_prob, 'away': away_prob}
    else:
        fair_probs = _remove_margin({'home': home_prob, 'draw': draw_prob, 'away': away_prob})

    # Normalize to 0-1 scale (excluding draw)
    home_prob = fair_probs['home']
    away_prob = fair_probs['away']
    total = home_prob + away_prob

    if total <= 0:
        return 0.5, 0.5

    return home_prob / total, away_prob / total


def get_odds_lambdas(home_team: str, away_team: str, season: Optional[int] = None) -> Tuple[float, float]:
    """
    Get expected goals (lambdas) from betting odds

    Args:
        home_team: Home team name
        away_team: Away team name
        season: Season year (defaults to current season)

    Returns:
        Tuple of (home_lambda, away_lambda)
    """
    if season is None:
        season = get_current_season()

    client = APIFootballClient()
    odds_data = client.get_match_odds(home_team, away_team, season)

    if not odds_data:
        return 1.7, 1.4  # Bundesliga averages

    # Prefer Betfair (fair odds), fallback to Pinnacle, then Bet365
    odds = odds_data.get('fair_odds') or odds_data.get('pinnacle') or odds_data.get('bet365')

    if not odds:
        return 1.7, 1.4

    # Convert to probabilities
    home_prob = _odds_to_probability(odds.get('home', 0))
    draw_prob = _odds_to_probability(odds.get('draw', 0))
    away_prob = _odds_to_probability(odds.get('away', 0))

    # Remove margin
    if odds == odds_data.get('fair_odds'):
        fair_probs = {'home': home_prob, 'draw': draw_prob, 'away': away_prob}
    else:
        fair_probs = _remove_margin({'home': home_prob, 'draw': draw_prob, 'away': away_prob})

    # Convert to lambdas
    return _probability_to_lambda(fair_probs['home'], fair_probs['draw'], fair_probs['away'])


def get_odds_data(home_team: str, away_team: str, season: Optional[int] = None) -> Optional[Dict]:
    """
    Get complete odds data for a match

    Args:
        home_team: Home team name
        away_team: Away team name
        season: Season year (defaults to current season)

    Returns:
        Complete odds data including all bookmakers
    """
    if season is None:
        season = get_current_season()

    client = APIFootballClient()
    return client.get_match_odds(home_team, away_team, season)


def main():
    """Test betting odds module"""

    print("=" * 80)
    print("Betting Odds Integration (API-Football) - Test")
    print("=" * 80)

    # IMPORTANT: Use season 2024 for 2024/25 season
    # (System date might be in future, causing season detection to return wrong year)
    season = 2024
    print(f"\nUsing season: {season} (2024/25)")
    print("=" * 80)

    test_matches = [
        ("Heidenheim", "Eintracht Frankfurt"),
        ("Augsburg", "Dortmund"),
        ("RB Leipzig", "VfB Stuttgart")
    ]

    for home, away in test_matches:
        print(f"\n{'='*80}")
        print(f"Match: {home} vs {away}")
        print('-' * 80)

        # Get complete odds data with explicit season
        odds_data = get_odds_data(home, away, season=season)

        if odds_data:
            print(f"\n📊 Odds from Multiple Bookmakers:")

            has_odds = False
            for bookmaker in ['pinnacle', 'betfair', 'bet365']:
                bm_odds = odds_data.get(bookmaker)
                if bm_odds:
                    has_odds = True
                    print(f"\n  {bookmaker.capitalize()}:")
                    print(f"    Home: {bm_odds.get('home', 'N/A'):.2f}")
                    print(f"    Draw: {bm_odds.get('draw', 'N/A'):.2f}")
                    print(f"    Away: {bm_odds.get('away', 'N/A'):.2f}")

            if not has_odds:
                print("  ⚠️  No bookmaker odds available")
                print(f"  Source: {odds_data.get('source', 'unknown')}")

            if odds_data.get('best_odds'):
                print(f"\n  Best Available:")
                print(f"    Home: {odds_data['best_odds']['home']:.2f}")
                print(f"    Draw: {odds_data['best_odds']['draw']:.2f}")
                print(f"    Away: {odds_data['best_odds']['away']:.2f}")

            # Get strengths for prediction
            home_str, away_str = get_odds_strength(home, away, season=season)
            print(f"\n✨ Normalized Strengths (for prediction):")
            print(f"  Home: {home_str:.1%}")
            print(f"  Away: {away_str:.1%}")

            # Get lambdas
            home_lambda, away_lambda = get_odds_lambdas(home, away, season=season)
            print(f"\n⚽ Expected Goals (from odds):")
            print(f"  Home: {home_lambda:.2f}")
            print(f"  Away: {away_lambda:.2f}")
        else:
            print("  ⚠️  No odds data available")

    print("\n" + "=" * 80)
    print("Betting Odds Test Completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
