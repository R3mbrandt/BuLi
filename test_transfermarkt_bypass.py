#!/usr/bin/env python3
"""
Test CloudScraper with Transfermarkt
"""

import cloudscraper

print("Testing CloudScraper with Transfermarkt...")
print("=" * 80)

scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

url = "https://www.transfermarkt.de/bundesliga/startseite/wettbewerb/L1"
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
