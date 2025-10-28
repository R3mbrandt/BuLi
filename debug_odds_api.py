#!/usr/bin/env python3
"""
Debug script to check why odds are not being fetched
"""

import sys
import os
sys.path.insert(0, 'src')

from data_sources.api_football import APIFootballClient

print("=" * 80)
print("Debugging Odds API")
print("=" * 80)

# Check API key
api_key = os.environ.get('API_FOOTBALL_KEY', None)
print(f"\n1. API Key Status:")
print(f"   Set: {'Yes' if api_key else 'No'}")
if api_key:
    print(f"   Preview: {api_key[:10]}...{api_key[-5:]}" if len(api_key) > 15 else "   (too short)")
else:
    print("   ⚠️  API key not set! Running in MOCK mode")

# Initialize client
print(f"\n2. Initializing APIFootballClient...")
client = APIFootballClient()
print(f"   Mock mode: {client.mock_mode}")

# Try to fetch fixtures for season 2024
print(f"\n3. Fetching fixtures for season 2024...")
fixtures = client.get_bundesliga_fixtures(season=2024)

if fixtures is not None and not fixtures.empty:
    print(f"   ✓ Got {len(fixtures)} fixtures")
    print(f"\n   Sample fixtures:")
    print(fixtures[['HomeTeam', 'AwayTeam', 'Date', 'Status']].head(3).to_string(index=False))

    # Find upcoming fixtures
    upcoming = fixtures[fixtures['Status'].isin(['NS', 'TBD'])]
    print(f"\n   Upcoming fixtures: {len(upcoming)}")
    if not upcoming.empty:
        print(upcoming[['HomeTeam', 'AwayTeam', 'Date']].head(3).to_string(index=False))
else:
    print("   ⚠️  No fixtures available")

# Try to fetch odds for a specific match
print(f"\n4. Testing odds fetch for Bayern vs Dortmund...")
odds = client.get_match_odds("Bayern", "Dortmund", season=2024)

if odds:
    print("   ✓ Got odds data:")
    print(f"   Pinnacle: {odds.get('pinnacle', 'None')}")
    print(f"   Betfair:  {odds.get('betfair', 'None')}")
    print(f"   Bet365:   {odds.get('bet365', 'None')}")
    print(f"   Source:   {odds.get('source', 'Unknown')}")
else:
    print("   ⚠️  No odds data returned")

print("\n" + "=" * 80)
print("Debug Complete")
print("=" * 80)

if client.mock_mode:
    print("\n⚠️  RUNNING IN MOCK MODE")
    print("To enable real API calls:")
    print("  export API_FOOTBALL_KEY='your-api-key'")
    print("\nGet your API key from:")
    print("  https://rapidapi.com/api-sports/api/api-football")
