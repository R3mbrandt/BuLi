#!/usr/bin/env python3
"""
Test odds parsing with Frankfurt vs St. Pauli (Fixture 1388375)
"""

import sys
import os
sys.path.insert(0, 'src')

# Set API key
os.environ['API_FOOTBALL_KEY'] = 'eb05b8d78736fa783e7c77b11370952a'

from data_sources.api_football import APIFootballClient
import json

print("=" * 80)
print("Testing Odds for Frankfurt vs St. Pauli (Fixture 1388375)")
print("=" * 80)

client = APIFootballClient()

# Test 1: Get fixture details
print("\n1. Getting fixture details...")
print("-" * 80)

response = client._make_request('/fixtures', {'id': 1388375})

if response and response.get('response'):
    fixture = response['response'][0]
    home = fixture['teams']['home']['name']
    away = fixture['teams']['away']['name']
    date = fixture['fixture']['date']
    status = fixture['fixture']['status']['long']

    print(f"✓ Fixture found:")
    print(f"  Home: {home}")
    print(f"  Away: {away}")
    print(f"  Date: {date}")
    print(f"  Status: {status}")
else:
    print("✗ Could not fetch fixture")
    sys.exit(1)

# Test 2: Get raw odds from API
print("\n2. Getting raw odds from API...")
print("-" * 80)

odds_response = client._make_request('/odds', {'fixture': 1388375})

if odds_response and odds_response.get('response'):
    print(f"✓ Got odds response")
    print(f"  Number of bookmakers: {len(odds_response['response'][0].get('bookmakers', []))}")

    # Show bookmaker names
    bookmakers = odds_response['response'][0].get('bookmakers', [])
    print(f"\n  Available bookmakers:")
    for bm in bookmakers[:10]:  # Show first 10
        print(f"    - {bm['name']} (ID: {bm['id']})")
    if len(bookmakers) > 10:
        print(f"    ... and {len(bookmakers) - 10} more")
else:
    print("✗ Could not fetch odds")
    sys.exit(1)

# Test 3: Parse odds using our function
print("\n3. Parsing odds with updated _parse_odds_response...")
print("-" * 80)

parsed_odds = client._parse_odds_response(odds_response['response'], home, away)

print(f"✓ Odds parsed successfully")
print(f"\nParsed odds:")
print(f"  Source: {parsed_odds.get('source')}")

for bookmaker in ['pinnacle', 'betfair', 'bet365']:
    odds = parsed_odds.get(bookmaker)
    if odds:
        print(f"\n  {bookmaker.capitalize()}:")
        print(f"    Home: {odds['home']:.2f}")
        print(f"    Draw: {odds['draw']:.2f}")
        print(f"    Away: {odds['away']:.2f}")
    else:
        print(f"\n  {bookmaker.capitalize()}: Not available")

if parsed_odds.get('fair_odds'):
    print(f"\n  Fair Odds (Betfair):")
    print(f"    Home: {parsed_odds['fair_odds']['home']:.2f}")
    print(f"    Draw: {parsed_odds['fair_odds']['draw']:.2f}")
    print(f"    Away: {parsed_odds['fair_odds']['away']:.2f}")

if parsed_odds.get('best_odds'):
    print(f"\n  Best Odds:")
    print(f"    Home: {parsed_odds['best_odds']['home']:.2f}")
    print(f"    Draw: {parsed_odds['best_odds']['draw']:.2f}")
    print(f"    Away: {parsed_odds['best_odds']['away']:.2f}")

# Test 4: Use high-level API
print("\n4. Testing high-level get_match_odds API...")
print("-" * 80)

# Clear cache first
cache_key = f"odds_{home}_{away}_2024"
if client.cache:
    import os
    cache_file = os.path.join(client.cache.cache_dir, f"{cache_key}.pkl")
    if os.path.exists(cache_file):
        os.remove(cache_file)
        print(f"  Cleared cache for {cache_key}")

odds = client.get_match_odds(home, away, season=2024)

if odds:
    print(f"✓ get_match_odds() successful")
    print(f"\nOdds for {home} vs {away}:")

    for bookmaker in ['pinnacle', 'betfair', 'bet365']:
        bm_odds = odds.get(bookmaker)
        if bm_odds:
            print(f"\n  {bookmaker.capitalize()}:")
            print(f"    Home: {bm_odds['home']:.2f}")
            print(f"    Draw: {bm_odds['draw']:.2f}")
            print(f"    Away: {bm_odds['away']:.2f}")
else:
    print("✗ get_match_odds() returned None")

# Test 5: Test betting_odds module
print("\n5. Testing betting_odds module integration...")
print("-" * 80)

from data_sources.betting_odds import get_odds_strength, get_odds_lambdas

home_str, away_str = get_odds_strength(home, away, season=2024)
print(f"✓ Odds strength:")
print(f"  Home: {home_str:.1%}")
print(f"  Away: {away_str:.1%}")

home_lambda, away_lambda = get_odds_lambdas(home, away, season=2024)
print(f"\n✓ Expected goals from odds:")
print(f"  Home: {home_lambda:.2f}")
print(f"  Away: {away_lambda:.2f}")

print("\n" + "=" * 80)
print("All tests completed!")
print("=" * 80)
