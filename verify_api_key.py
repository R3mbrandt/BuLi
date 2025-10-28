#!/usr/bin/env python3
"""
Verify API key and check API-Football subscription
"""

import requests
import os

API_KEY = os.environ.get('API_FOOTBALL_KEY', '')

print("=" * 80)
print("API-Football Key Verification")
print("=" * 80)
print(f"\nAPI Key: {API_KEY[:10]}...{API_KEY[-5:]}" if len(API_KEY) > 15 else f"\nAPI Key: {API_KEY}")
print(f"Length: {len(API_KEY)} characters")
print()

# Common API-Football endpoints to test
test_configs = [
    {
        'name': 'API-Football v3 (RapidAPI)',
        'url': 'https://v3.football.api-sports.io/timezone',
        'headers': {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': API_KEY
        }
    },
    {
        'name': 'API-Football v3 (Direct)',
        'url': 'https://v3.football.api-sports.io/timezone',
        'headers': {
            'x-apisports-key': API_KEY
        }
    },
    {
        'name': 'API-Sports (Alternative)',
        'url': 'https://api.api-football.com/v3/timezone',
        'headers': {
            'x-apisports-key': API_KEY
        }
    },
    {
        'name': 'API-Sports (Alternative with RapidAPI)',
        'url': 'https://api.api-football.com/v3/timezone',
        'headers': {
            'x-rapidapi-key': API_KEY
        }
    }
]

for config in test_configs:
    print(f"\n{config['name']}:")
    print("-" * 80)
    print(f"URL: {config['url']}")

    try:
        response = requests.get(
            config['url'],
            headers=config['headers'],
            timeout=10
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            print("✓ SUCCESS! This configuration works!")
            try:
                data = response.json()
                print(f"Response: {data}")

                # Check subscription info if available
                if 'response' in data:
                    print(f"\nTimezones available: {len(data['response'])}")
            except:
                print(f"Response text: {response.text[:200]}")
            break
        elif response.status_code == 401:
            print("✗ Unauthorized - API key may be invalid")
        elif response.status_code == 403:
            print("✗ Forbidden - Access denied")
            print(f"   Response: {response.text[:200]}")
        elif response.status_code == 429:
            print("✗ Rate limit exceeded")
        else:
            print(f"✗ Failed: {response.text[:200]}")

    except Exception as e:
        print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("Verification Complete")
print("=" * 80)
print("\nTroubleshooting:")
print("1. Verify your API key is active at: https://rapidapi.com/api-sports/api/api-football")
print("2. Check your subscription status")
print("3. Make sure you copied the entire API key")
print("4. Check if you have API requests remaining for today")
print("=" * 80)
