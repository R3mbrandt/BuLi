#!/usr/bin/env python3
"""
Direct test of FBrefScraper with cloudscraper
"""

from src.data_sources.fbref import FBrefScraper

print("Testing FBrefScraper with CloudScraper...")
print("=" * 80)

scraper = FBrefScraper()
print("✓ FBrefScraper initialized")

# Test getting league table
print("\nAttempting to fetch league table...")
table = scraper.get_league_table()

if not table.empty:
    print(f"✓ SUCCESS! Got {len(table)} teams")
    print(f"\nColumns: {list(table.columns)}")

    # Check for xG
    xg_cols = [col for col in table.columns if 'xG' in col]
    if xg_cols:
        print(f"✓ xG columns found: {xg_cols}")
        print(f"\nFirst 3 teams:")
        display_cols = ['Team'] + xg_cols
        display_cols = [col for col in display_cols if col in table.columns]
        print(table.head(3)[display_cols].to_string(index=False))
    else:
        print("⚠️  No xG columns")
else:
    print("✗ FAILED - empty table")

print("\n" + "=" * 80)
