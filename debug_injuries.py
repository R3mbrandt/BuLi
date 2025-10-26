#!/usr/bin/env python3
"""
Debug script to test Transfermarkt injury scraping
Shows detailed information about which team names are found
"""

import sys
from src.data_sources.transfermarkt import TransfermarktScraper

def main():
    """Test injury scraping with debug output"""

    scraper = TransfermarktScraper()

    print("=" * 80)
    print("TRANSFERMARKT INJURY SCRAPER - DEBUG MODE")
    print("=" * 80)

    # Test teams
    test_teams = [
        '1. FSV Mainz 05',
        'Mainz 05',
        'VfB Stuttgart',
        'Bayern München'
    ]

    print("\n1. Fetching all Bundesliga injuries with debug output...")
    print("-" * 80)

    # First, fetch and show all team names found
    all_injuries = scraper._fetch_all_bundesliga_injuries(debug=True)

    print("\n\n2. Testing specific team lookups...")
    print("-" * 80)

    for team in test_teams:
        print(f"\n{'=' * 80}")
        print(f"Testing: {team}")
        print(f"{'=' * 80}")

        result = scraper.get_injuries(team, debug=True)

        if result:
            print(f"\n✓ Result:")
            print(f"  Team queried: {result['team']}")
            print(f"  Team matched: {result.get('matched_team', 'N/A')}")
            print(f"  Injured count: {result['injured_count']}")
            if result['injured_players']:
                print(f"  Players:")
                for player in result['injured_players']:
                    print(f"    - {player['name']}: {player['injury']}")
        else:
            print(f"\n✗ No result found")

    print("\n" + "=" * 80)
    print("DEBUG TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    main()
