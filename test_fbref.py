#!/usr/bin/env python3
"""
Test script for FBref xG integration
Tests scraping and data extraction from FBref.com
"""

from src.data_sources.fbref import FBrefScraper
import pandas as pd

def test_fbref_integration():
    """Test FBref scraper with focus on xG data"""

    print("=" * 80)
    print("FBREF SCRAPER TEST - XG DATA EXTRACTION")
    print("=" * 80)

    scraper = FBrefScraper()

    # Test 1: Get league table with xG data
    print("\n1. Testing League Table (with xG data):")
    print("-" * 80)

    table = scraper.get_league_table()

    if not table.empty:
        print(f"✓ Successfully fetched league table: {len(table)} teams")
        print(f"\nColumns available: {list(table.columns)}")

        # Check if xG columns exist
        xg_cols = [col for col in table.columns if 'xG' in col]
        if xg_cols:
            print(f"✓ Found xG columns: {xg_cols}")
            print(f"\nTop 5 teams by xG:")
            display_cols = ['Team', 'Played', 'GoalsFor', 'GoalsAgainst'] + xg_cols
            display_cols = [col for col in display_cols if col in table.columns]
            if display_cols:
                print(table.head(5)[display_cols].to_string(index=False))
        else:
            print("⚠️  No xG columns found in league table")
            print(f"Available columns: {list(table.columns)}")
    else:
        print("✗ Failed to fetch league table")

    # Test 2: Get match results with xG
    print("\n\n2. Testing Recent Match Results (with xG):")
    print("-" * 80)

    matches = scraper.get_match_results(limit=10)

    if not matches.empty:
        print(f"✓ Successfully fetched {len(matches)} matches")
        print(f"\nColumns available: {list(matches.columns)}")

        # Check if xG columns exist
        if 'xG_Home' in matches.columns and 'xG_Away' in matches.columns:
            print(f"✓ Found xG data in match results")
            print(f"\nLast 5 matches with xG:")
            display_cols = ['Date', 'HomeTeam', 'AwayTeam', 'Score', 'xG_Home', 'xG_Away']
            display_cols = [col for col in display_cols if col in matches.columns]
            if display_cols:
                print(matches.tail(5)[display_cols].to_string(index=False))
        else:
            print("⚠️  No xG columns found in match results")
            print(f"Available columns: {list(matches.columns)}")
    else:
        print("✗ Failed to fetch match results")

    # Test 3: Get specific team xG stats
    print("\n\n3. Testing Team xG Statistics:")
    print("-" * 80)

    xg_stats = scraper.get_team_xg_stats()

    if not xg_stats.empty:
        print(f"✓ Successfully fetched xG stats: {len(xg_stats)} teams")
        print(f"\nColumns available: {list(xg_stats.columns)}")
        print(f"\nAll xG data:")
        print(xg_stats.to_string(index=False))
    else:
        print("✗ Failed to fetch xG statistics")

    # Test 4: Check specific teams
    print("\n\n4. Testing Specific Team Lookup (Stuttgart & Mainz):")
    print("-" * 80)

    test_teams = ['Stuttgart', 'Mainz']

    if not table.empty and 'Team' in table.columns:
        for team in test_teams:
            team_data = table[table['Team'].str.contains(team, case=False, na=False)]
            if not team_data.empty:
                print(f"\n✓ Found {team}:")
                print(f"  Full name: {team_data['Team'].values[0]}")

                # Show xG data if available
                if 'xG' in team_data.columns:
                    print(f"  xG: {team_data['xG'].values[0]}")
                if 'xGA' in team_data.columns:
                    print(f"  xGA: {team_data['xGA'].values[0]}")
                if 'xGDiff' in team_data.columns:
                    print(f"  xG Diff: {team_data['xGDiff'].values[0]}")
            else:
                print(f"\n✗ {team} not found in table")

    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    success_count = 0
    total_tests = 3

    if not table.empty:
        success_count += 1
        print("✓ League table: SUCCESS")
    else:
        print("✗ League table: FAILED")

    if not matches.empty:
        success_count += 1
        print("✓ Match results: SUCCESS")
    else:
        print("✗ Match results: FAILED")

    if not xg_stats.empty:
        success_count += 1
        print("✓ xG statistics: SUCCESS")
    else:
        print("✗ xG statistics: FAILED")

    print(f"\nScore: {success_count}/{total_tests} tests passed")

    # Check if xG data is available
    has_xg = False
    if not table.empty:
        xg_cols = [col for col in table.columns if 'xG' in col]
        if xg_cols:
            has_xg = True

    if has_xg:
        print("✓ xG data is AVAILABLE and ready for integration")
    else:
        print("⚠️  xG data may not be available - will use goals as fallback")

    print("=" * 80)

if __name__ == "__main__":
    test_fbref_integration()
