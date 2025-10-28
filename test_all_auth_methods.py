#!/usr/bin/env python3
"""
Test all possible authentication methods for API-Football
"""

import requests
import os

API_KEY = os.environ.get('API_FOOTBALL_KEY', 'eb05b8d78736fa783e7c77b11370952a')
FIXTURE_ID = 1388375

print("=" * 80)
print("Testing All Authentication Methods")
print("=" * 80)
print(f"\nAPI Key: {API_KEY}")
print(f"Testing with fixture ID: {FIXTURE_ID}")
print()

# Different authentication configurations to test
configs = [
    {
        'name': 'Method 1: x-apisports-key header',
        'url': 'https://v3.football.api-sports.io/fixtures',
        'headers': {'x-apisports-key': API_KEY},
        'params': {'id': FIXTURE_ID}
    },
    {
        'name': 'Method 2: x-rapidapi-key header',
        'url': 'https://v3.football.api-sports.io/fixtures',
        'headers': {
            'x-rapidapi-key': API_KEY,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        },
        'params': {'id': FIXTURE_ID}
    },
    {
        'name': 'Method 3: apikey query parameter',
        'url': 'https://v3.football.api-sports.io/fixtures',
        'headers': {},
        'params': {'id': FIXTURE_ID, 'apikey': API_KEY}
    },
    {
        'name': 'Method 4: api_key query parameter',
        'url': 'https://v3.football.api-sports.io/fixtures',
        'headers': {},
        'params': {'id': FIXTURE_ID, 'api_key': API_KEY}
    },
    {
        'name': 'Method 5: Authorization Bearer',
        'url': 'https://v3.football.api-sports.io/fixtures',
        'headers': {'Authorization': f'Bearer {API_KEY}'},
        'params': {'id': FIXTURE_ID}
    },
    {
        'name': 'Method 6: Authorization key',
        'url': 'https://v3.football.api-sports.io/fixtures',
        'headers': {'Authorization': API_KEY},
        'params': {'id': FIXTURE_ID}
    },
    {
        'name': 'Method 7: x-api-key header',
        'url': 'https://v3.football.api-sports.io/fixtures',
        'headers': {'x-api-key': API_KEY},
        'params': {'id': FIXTURE_ID}
    },
    {
        'name': 'Method 8: API-Key header',
        'url': 'https://v3.football.api-sports.io/fixtures',
        'headers': {'API-Key': API_KEY},
        'params': {'id': FIXTURE_ID}
    },
]

for i, config in enumerate(configs, 1):
    print(f"{i}. {config['name']}")
    print("-" * 80)

    try:
        response = requests.get(
            config['url'],
            headers=config['headers'],
            params=config['params'],
            timeout=10
        )

        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print("   ✓ SUCCESS! This method works!")
            data = response.json()

            if data.get('response'):
                fixture = data['response'][0]
                print(f"   Home: {fixture['teams']['home']['name']}")
                print(f"   Away: {fixture['teams']['away']['name']}")
                print(f"   Date: {fixture['fixture']['date']}")

            print("\n" + "=" * 80)
            print("FOUND WORKING METHOD!")
            print("=" * 80)
            print(f"Headers: {config['headers']}")
            print(f"Params: {config['params']}")
            break
        elif response.status_code == 401:
            print("   ✗ 401 Unauthorized")
        elif response.status_code == 403:
            print("   ✗ 403 Forbidden")
        elif response.status_code == 429:
            print("   ✗ 429 Rate Limit")
        else:
            print(f"   ✗ {response.status_code}: {response.text[:100]}")

    except Exception as e:
        print(f"   ✗ Error: {e}")

    print()

print("=" * 80)
print("All methods tested")
print("=" * 80)
print("\nIf none worked, please:")
print("1. Verify your API key at: https://dashboard.api-football.com/")
print("2. Check your subscription is active")
print("3. Check rate limits")
print("4. Verify account email is confirmed")
