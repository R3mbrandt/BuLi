#!/usr/bin/env python3
"""
Raw cloudscraper test - exactly as in test_fbref_bypass.py
"""

import cloudscraper

print("Testing cloudscraper raw...")
print("=" * 80)

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

url = "https://fbref.com/en/comps/20/Bundesliga-Stats"
print(f"Fetching: {url}")

try:
    response = scraper.get(url, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.content)}")

    if 'Bundesliga' in response.text:
        print("✓ SUCCESS - Contains 'Bundesliga'")
    else:
        print("✗ No 'Bundesliga' found")

except Exception as e:
    print(f"✗ Error: {e}")

print("=" * 80)
