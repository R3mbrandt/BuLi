#!/usr/bin/env python3
"""
Test direct API-Football (api-sports.io) with specific fixture
"""

import requests
import os
import json

API_KEY = os.environ.get('API_FOOTBALL_KEY', 'eb05b8d78736fa783e7c77b11370952a')
BASE_URL = "https://v3.football.api-sports.io"

print("=" * 80)
print("Testing Direct API-Football (api-sports.io)")
print("=" * 80)
print(f"\nAPI Key: {API_KEY[:10]}...{API_KEY[-5:]}")
print(f"Base URL: {BASE_URL}")

# Test 1: Status endpoint
print("\n1. Testing /status endpoint:")
print("-" * 80)

headers = {
    'x-apisports-key': API_KEY
}

try:
    response = requests.get(
        f"{BASE_URL}/status",
        headers=headers,
        timeout=10
    )
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✓ API Key is valid!")
        data = response.json()
        print(f"\nAPI Response:")
        print(json.dumps(data, indent=2))
    else:
        print(f"✗ Failed: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Specific fixture (Frankfurt vs St. Pauli)
print("\n2. Testing fixture 1388375 (Frankfurt vs St. Pauli, 25.10.2025):")
print("-" * 80)

fixture_id = 1388375

try:
    response = requests.get(
        f"{BASE_URL}/fixtures",
        headers=headers,
        params={'id': fixture_id},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✓ Fixture data retrieved!")
        data = response.json()

        if data.get('response'):
            fixture = data['response'][0]
            print(f"\nFixture Details:")
            print(f"  Home: {fixture['teams']['home']['name']}")
            print(f"  Away: {fixture['teams']['away']['name']}")
            print(f"  Date: {fixture['fixture']['date']}")
            print(f"  Status: {fixture['fixture']['status']['long']}")

            # Show goals if available
            if fixture.get('goals'):
                print(f"  Score: {fixture['goals']['home']} - {fixture['goals']['away']}")
    else:
        print(f"✗ Failed: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Odds for specific fixture
print("\n3. Testing odds for fixture 1388375:")
print("-" * 80)

try:
    response = requests.get(
        f"{BASE_URL}/odds",
        headers=headers,
        params={'fixture': fixture_id},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✓ Odds data retrieved!")
        data = response.json()

        if data.get('response') and len(data['response']) > 0:
            print(f"\nFound {len(data['response'])} bookmakers")

            # Look for specific bookmakers
            bookmakers_found = {}
            for item in data['response']:
                bm_name = item['bookmaker']['name']
                bookmakers_found[bm_name] = item

            # Show Betfair, Pinnacle, Bet365 if available
            for bm in ['Betfair', 'Pinnacle Sports', 'Bet365']:
                if bm in bookmakers_found:
                    print(f"\n  {bm}:")
                    bets = bookmakers_found[bm].get('bets', [])
                    for bet in bets:
                        if bet['name'] == 'Match Winner':
                            for value in bet['values']:
                                print(f"    {value['value']}: {value['odd']}")
        else:
            print("  ⚠️  No odds available for this fixture")
    else:
        print(f"✗ Failed: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 4: Bundesliga fixtures for season 2024
print("\n4. Testing Bundesliga fixtures (season 2024):")
print("-" * 80)

try:
    response = requests.get(
        f"{BASE_URL}/fixtures",
        headers=headers,
        params={'league': 78, 'season': 2024, 'last': 5},
        timeout=10
    )
    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✓ Fixtures retrieved!")
        data = response.json()

        if data.get('response'):
            print(f"\nLast 5 Bundesliga fixtures:")
            for fixture in data['response'][:5]:
                print(f"  {fixture['teams']['home']['name']} vs {fixture['teams']['away']['name']}")
                print(f"    Date: {fixture['fixture']['date'][:10]}")
    else:
        print(f"✗ Failed: {response.text}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
