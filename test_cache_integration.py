#!/usr/bin/env python3
"""
Test cache integration for all data sources
"""

print("=" * 80)
print("Testing Cache Integration")
print("=" * 80)

# Test 1: Cache module
print("\n1. Testing cache module...")
try:
    from src.data_sources.cache import get_cache
    cache = get_cache()
    print("   ✓ Cache module loaded successfully")

    # Test set/get
    cache.set("test_key", {"value": 123})
    result = cache.get("test_key")
    if result and result.get("value") == 123:
        print("   ✓ Cache set/get works")
    else:
        print("   ✗ Cache set/get failed")

except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Transfermarkt with cache
print("\n2. Testing Transfermarkt with cache...")
try:
    from src.data_sources.transfermarkt import TransfermarktScraper
    scraper = TransfermarktScraper(use_cache=True)
    print("   ✓ TransfermarktScraper initialized with cache")
    print(f"   ✓ Cache enabled: {scraper.use_cache}")
    print(f"   ✓ Cache expiry: {scraper.cache_expiry_hours}h")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: FBref with cache
print("\n3. Testing FBref with cache...")
try:
    from src.data_sources.fbref import FBrefScraper
    scraper = FBrefScraper(use_cache=True)
    print("   ✓ FBrefScraper initialized with cache")
    print(f"   ✓ Cache enabled: {scraper.use_cache}")
    print(f"   ✓ Cache expiry: {scraper.cache_expiry_hours}h")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 4: ELO with cache
print("\n4. Testing ELO Rating System with cache...")
try:
    from src.models.elo_rating import ELORatingSystem
    elo = ELORatingSystem(use_cache=True)
    print("   ✓ ELORatingSystem initialized with cache")
    print(f"   ✓ Cache enabled: {elo.use_cache}")
    print(f"   ✓ Cache expiry: {elo.cache_expiry_hours}h")

    # Test save/load
    elo.ratings = {"Test Team": 1500.0}
    elo.save_ratings_to_cache("test_elo")

    elo2 = ELORatingSystem(use_cache=True)
    elo2.load_ratings_from_cache("test_elo")
    if "Test Team" in elo2.ratings:
        print("   ✓ ELO cache save/load works")
    else:
        print("   ✗ ELO cache save/load failed")

except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 5: List cache files
print("\n5. Cache files created:")
try:
    import os
    cache_dir = ".cache"
    if os.path.exists(cache_dir):
        files = os.listdir(cache_dir)
        if files:
            for f in files:
                size = os.path.getsize(os.path.join(cache_dir, f))
                print(f"   - {f} ({size} bytes)")
        else:
            print("   (No cache files yet - will be created on first use)")
    else:
        print("   (Cache directory doesn't exist yet)")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 80)
print("Cache Integration Test Complete!")
print("=" * 80)

# Summary
print("\n📋 CACHE KEY SUMMARY:")
print("-" * 80)
print("Transfermarkt:")
print("  - squad_value_{team_name}")
print("  - bundesliga_injuries_all")
print("\nFBref:")
print("  - fbref_league_table_{season}")
print("  - fbref_match_results_{season}_{limit}")
print("  - fbref_team_xg_{season}")
print("\nELO Ratings:")
print("  - elo_ratings_bundesliga (default)")
print("\nCache expiry: 24 hours (default)")
print("Cache location: .cache/ directory")
print("-" * 80)
