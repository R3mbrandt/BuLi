#!/usr/bin/env python3
"""
Test with minimal headers (only what curl uses)
"""

import requests

API_KEY = 'eb05b8d78736fa783e7c77b11370952a'

print("=" * 80)
print("Testing with Minimal Headers (like curl)")
print("=" * 80)

# Test 1: Only x-apisports-key (no RapidAPI headers)
print("\n1. Test with ONLY x-apisports-key:")
print("-" * 80)

session = requests.Session()
session.headers.update({
    'x-apisports-key': API_KEY
})

print(f"Headers: {dict(session.headers)}")

try:
    response = session.get(
        'https://v3.football.api-sports.io/status',
        timeout=30
    )

    print(f"\nStatus Code: {response.status_code}")

    if response.status_code == 200:
        print("✓ SUCCESS!")
        data = response.json()
        print(f"\nAccount: {data['response']['account']}")
        print(f"Subscription: {data['response']['subscription']}")
        print(f"Requests: {data['response']['requests']}")
    else:
        print(f"✗ Failed: {response.text[:200]}")

except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Try fixture 1388375
print("\n\n2. Test fixture 1388375:")
print("-" * 80)

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
            print(f"\nHome: {fixture['teams']['home']['name']}")
            print(f"Away: {fixture['teams']['away']['name']}")
            print(f"Date: {fixture['fixture']['date']}")
    else:
        print(f"✗ Failed: {response.text[:200]}")

except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
