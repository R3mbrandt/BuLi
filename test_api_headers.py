#!/usr/bin/env python3
"""
Test different API header configurations
"""

import requests
import os

API_KEY = os.environ.get('API_FOOTBALL_KEY', '')
BASE_URL = "https://v3.football.api-sports.io"

print("=" * 80)
print("Testing API-Football Header Configurations")
print("=" * 80)

# Test 1: RapidAPI headers (current implementation)
print("\n1. Testing with RapidAPI headers:")
print("-" * 80)

headers_rapid = {
    'x-rapidapi-host': 'v3.football.api-sports.io',
    'x-rapidapi-key': API_KEY
}

try:
    response = requests.get(
        f"{BASE_URL}/status",
        headers=headers_rapid,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ RapidAPI headers work!")
        print(f"Response: {response.json()}")
    else:
        print(f"✗ Failed: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 2: Direct API-Football headers
print("\n2. Testing with direct API-Football headers:")
print("-" * 80)

headers_direct = {
    'x-apisports-key': API_KEY
}

try:
    response = requests.get(
        f"{BASE_URL}/status",
        headers=headers_direct,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ Direct API-Football headers work!")
        print(f"Response: {response.json()}")
    else:
        print(f"✗ Failed: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: Simple API key in header
print("\n3. Testing with x-api-key header:")
print("-" * 80)

headers_simple = {
    'x-api-key': API_KEY
}

try:
    response = requests.get(
        f"{BASE_URL}/status",
        headers=headers_simple,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✓ x-api-key headers work!")
        print(f"Response: {response.json()}")
    else:
        print(f"✗ Failed: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 80)
print("Header Test Complete!")
print("=" * 80)
