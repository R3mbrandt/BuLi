#!/usr/bin/env python3
"""
Test xG data fetching from API-Football
Test match: Heidenheim vs Frankfurt (01.11.2024)
"""

import sys
sys.path.insert(0, 'src')

from data_sources.api_football import APIFootballClient

print("=" * 80)
print("Testing xG Data from API-Football")
print("Test Match: Heidenheim vs Frankfurt (01.11.2024)")
print("=" * 80)

client = APIFootballClient()

# Test 1: Get match xG
print("\n1. Getting xG for specific match:")
print("-" * 80)

xg_data = client.get_match_xg("Heidenheim", "Frankfurt", season=2024)

if xg_data:
    print(f"Match: {xg_data['home_team']} vs {xg_data['away_team']}")
    print(f"  Home xG: {xg_data['home_xg']}")
    print(f"  Away xG: {xg_data['away_xg']}")
else:
    print("⚠️  No xG data available for this match")

# Test 2: Get team xG stats for season
print("\n2. Getting team xG statistics for season 2024:")
print("-" * 80)

team_stats = client.get_team_xg_stats(season=2024)

if team_stats is not None and not team_stats.empty:
    print(f"✓ Got xG stats for {len(team_stats)} teams")
    print("\nTop 5 teams by xG For:")
    print(team_stats.head(5).to_string(index=False))

    # Find Heidenheim and Frankfurt
    print("\nHeidenheim and Frankfurt stats:")
    for team in ['Heidenheim', 'Frankfurt']:
        team_data = team_stats[team_stats['Team'].str.contains(team, case=False, na=False)]
        if not team_data.empty:
            print(team_data.to_string(index=False))
else:
    print("⚠️  No team xG stats available")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
