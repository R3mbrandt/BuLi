#!/usr/bin/env python3
"""
Test with curl's User-Agent
"""

import requests

API_KEY = 'eb05b8d78736fa783e7c77b11370952a'

print("=" * 80)
print("Testing with curl User-Agent")
print("=" * 80)

# Mimic curl exactly
session = requests.Session()
session.headers.update({
    'User-Agent': 'curl/8.7.1',  # Same as in your curl
    'x-apisports-key': API_KEY
})

print(f"\nHeaders:")
for k, v in session.headers.items():
    if 'key' in k.lower():
        print(f"  {k}: {v[:10]}...{v[-5:]}")
    else:
        print(f"  {k}: {v}")

# Test 1: Status endpoint
print("\n" + "=" * 80)
print("Test 1: /status endpoint")
print("=" * 80)

try:
    response = session.get(
        'https://v3.football.api-sports.io/status',
        timeout=30
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✓ SUCCESS with curl User-Agent!")
        data = response.json()
        print(f"\nAccount: {data['response']['account']['firstname']} {data['response']['account']['lastname']}")
        print(f"Plan: {data['response']['subscription']['plan']}")
        print(f"Active: {data['response']['subscription']['active']}")
        print(f"Requests: {data['response']['requests']['current']}/{data['response']['requests']['limit_day']}")
    else:
        print(f"✗ Failed: {response.text[:200]}")

except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Fixture 1388375
print("\n" + "=" * 80)
print("Test 2: Fixture 1388375 (Frankfurt vs St. Pauli)")
print("=" * 80)

try:
    response = session.get(
        'https://v3.football.api-sports.io/fixtures',
        params={'id': 1388375},
        timeout=30
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✓ SUCCESS!")
        data = response.json()
        if data.get('response'):
            fixture = data['response'][0]
            print(f"\nFixture ID: {fixture['fixture']['id']}")
            print(f"Home: {fixture['teams']['home']['name']}")
            print(f"Away: {fixture['teams']['away']['name']}")
            print(f"Date: {fixture['fixture']['date']}")
            print(f"Status: {fixture['fixture']['status']['long']}")

            # Check for score
            if fixture.get('goals'):
                print(f"Score: {fixture['goals']['home']} - {fixture['goals']['away']}")
    else:
        print(f"✗ Failed: {response.text[:200]}")

except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Odds for fixture
print("\n" + "=" * 80)
print("Test 3: Odds for fixture 1388375")
print("=" * 80)

try:
    response = session.get(
        'https://v3.football.api-sports.io/odds',
        params={'fixture': 1388375},
        timeout=30
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        print("✓ SUCCESS!")
        data = response.json()

        if data.get('response') and len(data['response']) > 0:
            print(f"\nFound {len(data['response'])} bookmakers with odds")

            # Look for specific bookmakers
            for item in data['response']:
                bm_name = item['bookmaker']['name']
                if bm_name in ['Betfair', 'Pinnacle Sports', 'Bet365']:
                    print(f"\n{bm_name}:")
                    bets = item.get('bets', [])
                    for bet in bets:
                        if bet['name'] == 'Match Winner':
                            for value in bet['values']:
                                print(f"  {value['value']}: {value['odd']}")
        else:
            print("  No odds data available for this fixture")
    else:
        print(f"✗ Failed: {response.text[:200]}")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
