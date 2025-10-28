#!/bin/bash
# Setup script for API-Football odds testing

echo "=============================================================================="
echo "API-Football Odds Setup & Test"
echo "=============================================================================="
echo ""

# Check if API key is provided
if [ -z "$1" ]; then
    echo "Usage: ./setup_and_test_odds.sh YOUR_API_KEY"
    echo ""
    echo "Example:"
    echo "  ./setup_and_test_odds.sh abc123xyz456..."
    echo ""
    echo "Get your API key from:"
    echo "  https://rapidapi.com/api-sports/api/api-football"
    exit 1
fi

API_KEY="$1"

echo "1. Setting API key..."
export API_FOOTBALL_KEY="$API_KEY"
echo "   ✓ API_FOOTBALL_KEY set"

echo ""
echo "2. Clearing old cache..."
rm -f .cache/odds_*.pkl .cache/fixtures_*.pkl
echo "   ✓ Cache cleared"

echo ""
echo "3. Running debug script..."
echo ""
python debug_odds_api.py

echo ""
echo "=============================================================================="
echo ""
echo "4. Testing odds with real matches (Season 2024)..."
echo ""
python test_odds_season2024.py

echo ""
echo "=============================================================================="
echo "Setup & Test Complete!"
echo "=============================================================================="
