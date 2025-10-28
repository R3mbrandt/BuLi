# API-Football Setup Guide

This project now uses **API-Football** (via RapidAPI) for:
- ✅ Betting odds from Pinnacle, Betfair Exchange, and Bet365
- ✅ Bundesliga fixtures and results
- ✅ League standings/table
- ✅ Team statistics (for future backtesting)

## 🔑 Getting Your API Key

### Step 1: Sign Up for RapidAPI

1. Go to [RapidAPI](https://rapidapi.com/)
2. Create a free account
3. Navigate to [API-Football](https://rapidapi.com/api-sports/api/api-football)
4. Subscribe to a plan:
   - **Free**: 100 requests/day (good for testing)
   - **Pro**: ~$30/month, 3000 requests/day (recommended for regular use)
   - **Ultra**: ~$100/month, 10000 requests/day (for heavy usage)

### Step 2: Get Your API Key

1. After subscribing, go to the API-Football page
2. Click on "Code Snippets" or "Endpoints"
3. Your API key will be shown in the headers:
   ```
   x-rapidapi-key: YOUR_API_KEY_HERE
   ```
4. Copy this key

## 🛠️ Setting Up the API Key

### Option 1: Environment Variable (Recommended)

**Linux/Mac:**
```bash
export API_FOOTBALL_KEY="your-api-key-here"
```

**Windows (PowerShell):**
```powershell
$env:API_FOOTBALL_KEY="your-api-key-here"
```

**Permanent Setup (Linux/Mac):**
Add to your `~/.bashrc` or `~/.zshrc`:
```bash
echo 'export API_FOOTBALL_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Option 2: Create config.py (Not Recommended - for development only)

Create `src/config.py`:
```python
# API Keys
API_FOOTBALL_KEY = "your-api-key-here"
```

Then update `src/data_sources/api_football.py` line 24:
```python
from config import API_FOOTBALL_KEY
```

**⚠️ Warning**: Do NOT commit `config.py` to git! Add it to `.gitignore`.

## 📊 Testing Your Setup

### Test API-Football Client

```bash
python src/data_sources/api_football.py
```

Expected output:
```
✓ API-Football Client working
✓ Fetching odds from Pinnacle, Betfair, Bet365
✓ xG data availability check
```

### Test Betting Odds Module

```bash
python src/data_sources/betting_odds.py
```

Expected output:
```
✓ Odds from multiple bookmakers
✓ Fair probabilities (Betfair)
✓ Expected goals from odds
```

### Test Full Prediction with Odds

```bash
python predict.py --team1 "Bayern München" --team2 "VfL Bochum" --use-odds
```

Expected output:
```
✓ Odds integrated into prediction
✓ Factor Breakdown shows Odds: Home X% | Away Y%
```

## 🎯 Usage Examples

### Standard Prediction (without odds)
```bash
python predict.py --team1 "Bayern" --team2 "Dortmund"
```

### With Odds as Factor
```bash
python predict.py --team1 "Bayern" --team2 "Dortmund" --use-odds
```

### With Odds Calibration
```bash
python predict.py --team1 "Bayern" --team2 "Dortmund" --use-odds --odds-mode calibration
```

### Full Matchday with Odds
```bash
python predict.py --matchday 15 --use-odds
```

## 🔍 What Data is Fetched?

### With API Key:
- **Real odds** from Pinnacle, Betfair Exchange, Bet365
- **Live fixtures** and results
- **Bundesliga standings**
- **Team statistics** (for backtesting)

### Without API Key (Mock Mode):
- **Simulated odds** based on team strength
- **Cached/Mock fixtures** from OpenLigaDB
- All features work, but with sample data

## 💰 API Usage Optimization

To minimize API calls and stay within limits:

1. **Caching**: Data is cached automatically:
   - Odds: 6 hours
   - Fixtures: 24 hours
   - Standings: 24 hours

2. **Free Tier Tips** (100 requests/day):
   - ~3-5 matches per day with odds
   - Fixtures/standings refresh once daily
   - Perfect for testing and following specific teams

3. **Pro Tier** (3000 requests/day):
   - All matchday predictions (~9 matches)
   - Multiple seasons for backtesting
   - Historical data analysis

## 🚨 Troubleshooting

### "No API key" Warning
```
⚠️  Running in MOCK MODE (no API key)
```
→ Set `API_FOOTBALL_KEY` environment variable

### "403 Forbidden" Error
→ Check your API key is correct
→ Verify your RapidAPI subscription is active
→ Check API request limits

### "No fixtures data from API"
→ API might be down temporarily
→ Falls back to mock data automatically
→ Check RapidAPI status

## 📈 Upgrading Your Plan

As your needs grow:

1. **Start Free**: Test the integration (100 requests/day)
2. **Upgrade to Pro**: Daily matchday predictions ($30/month)
3. **Upgrade to Ultra**: Full backtesting + all leagues ($100/month)

## 🎁 Benefits of API-Football

### Odds
- ✅ **Betfair Exchange** = Fair odds (no bookmaker margin!)
- ✅ **Pinnacle** = Professional odds (lowest margin)
- ✅ **Bet365** = Popular bookmaker (good coverage)

### Data Quality
- ✅ Real-time updates
- ✅ Historical data back to 2008
- ✅ Consistent format across leagues
- ✅ One API for everything

### Future Features (with your API key)
- 🔜 Backtesting with 3+ seasons of data
- 🔜 Lambda optimization using historical matches
- 🔜 Multi-league support (Premier League, La Liga, etc.)
- 🔜 Live odds tracking

---

**Ready to go?** Set your API key and start making predictions with real market data! 🚀
