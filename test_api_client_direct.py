#!/usr/bin/env python3
"""
Test the updated APIFootballClient with direct API
"""

import sys
import os
sys.path.insert(0, 'src')

# Set API key
os.environ['API_FOOTBALL_KEY'] = 'eb05b8d78736fa783e7c77b11370952a'

from data_sources.api_football import APIFootballClient

print("=" * 80)
print("Testing Updated APIFootballClient")
print("=" * 80)

client = APIFootballClient()

print(f"\nAPI Key: {client.api_key[:10]}...{client.api_key[-5:]}")
print(f"Mock Mode: {client.mock_mode}")
print(f"\nSession Headers:")
for key, value in client.session.headers.items():
    if 'key' in key.lower():
        print(f"  {key}: {value[:10]}...{value[-5:]}" if len(value) > 15 else f"  {key}: {value}")
    else:
        print(f"  {key}: {value}")

# Test 1: Get fixtures for specific fixture ID
print("\n" + "=" * 80)
print("Test 1: Fetch specific fixture (1388375)")
print("=" * 80)

# Direct test using _make_request
response = client._make_request('/fixtures', {'id': 1388375})

if response:
    print("✓ Request successful!")
    if response.get('response'):
        fixture = response['response'][0]
        print(f"\nFixture Details:")
        print(f"  Home: {fixture['teams']['home']['name']}")
        print(f"  Away: {fixture['teams']['away']['name']}")
        print(f"  Date: {fixture['fixture']['date']}")
        print(f"  Status: {fixture['fixture']['status']['long']}")
else:
    print("✗ Request failed")

# Test 2: Get Bundesliga fixtures
print("\n" + "=" * 80)
print("Test 2: Get Bundesliga fixtures (season 2024)")
print("=" * 80)

fixtures = client.get_bundesliga_fixtures(season=2024)

if fixtures is not None and not fixtures.empty:
    print(f"✓ Got {len(fixtures)} fixtures")
    print(f"\nSample fixtures:")
    print(fixtures[['HomeTeam', 'AwayTeam', 'Date', 'Status']].head(3).to_string(index=False))
else:
    print("✗ No fixtures retrieved")

# Test 3: Get odds for Frankfurt vs St. Pauli
print("\n" + "=" * 80)
print("Test 3: Get odds for Frankfurt vs St. Pauli")
print("=" * 80)

odds = client.get_match_odds("Frankfurt", "St. Pauli", season=2024)

if odds:
    print("✓ Got odds data!")
    print(f"\nBookmakers:")
    for bm in ['pinnacle', 'betfair', 'bet365']:
        if odds.get(bm):
            print(f"  {bm.capitalize()}: {odds[bm]}")
else:
    print("✗ No odds retrieved")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
