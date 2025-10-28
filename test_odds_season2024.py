#!/usr/bin/env python3
"""
Test Betting Odds with explicit season 2024
This fixes the issue where system date (2025-10-28) causes season detection to use 2025
"""

import sys
sys.path.insert(0, 'src')

from data_sources.betting_odds import get_odds_strength, get_odds_lambdas, get_odds_data

print("=" * 80)
print("Betting Odds Test - Season 2024 (2024/25)")
print("=" * 80)

# Test matches with EXPLICIT season=2024
test_matches = [
    ("Heidenheim", "Eintracht Frankfurt"),
    ("Augsburg", "Dortmund"),
    ("RB Leipzig", "VfB Stuttgart"),
]

for home, away in test_matches:
    print(f"\n{'=' * 80}")
    print(f"Match: {home} vs {away}")
    print("-" * 80)

    # IMPORTANT: Use season=2024 explicitly
    odds_data = get_odds_data(home, away, season=2024)

    if odds_data:
        print("\n📊 Odds from Multiple Bookmakers:")

        if odds_data.get('pinnacle'):
            print(f"  Pinnacle:  {odds_data['pinnacle']}")
        if odds_data.get('betfair'):
            print(f"  Betfair:   {odds_data['betfair']}")
        if odds_data.get('bet365'):
            print(f"  Bet365:    {odds_data['bet365']}")
        if odds_data.get('fair_odds'):
            print(f"  Fair Odds: {odds_data['fair_odds']}")

        if not any([odds_data.get('pinnacle'), odds_data.get('betfair'), odds_data.get('bet365')]):
            print("  ⚠️  No bookmaker odds found!")
    else:
        print("  ⚠️  No odds data available")

    # Get normalized strengths
    home_str, away_str = get_odds_strength(home, away, season=2024)
    print(f"\n✨ Normalized Strengths (for prediction):")
    print(f"  Home: {home_str*100:.1f}%")
    print(f"  Away: {away_str*100:.1f}%")

    # Get expected goals from odds
    home_lambda, away_lambda = get_odds_lambdas(home, away, season=2024)
    print(f"\n⚽ Expected Goals (from odds):")
    print(f"  Home: {home_lambda:.2f}")
    print(f"  Away: {away_lambda:.2f}")

print("\n" + "=" * 80)
print("Test Completed!")
print("=" * 80)
print("\nNOTE: If you see 50.0%/50.0% and 1.70/1.40 everywhere,")
print("it means the API returned no odds (using fallback values).")
print("\nTo fix:")
print("1. Set your API key: export API_FOOTBALL_KEY='your-key'")
print("2. Make sure the matches have future fixtures with odds")
print("=" * 80)
