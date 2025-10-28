"""
API-Football Integration
Comprehensive football data API including odds, fixtures, standings, and statistics

API Documentation: https://www.api-football.com/documentation-v3
RapidAPI: https://rapidapi.com/api-sports/api/api-football

Features:
- Live and pre-match odds from multiple bookmakers (Pinnacle, Betfair, Bet365)
- Fixtures and results
- League standings
- Team statistics
- Historical data for backtesting
"""

import requests
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import os

try:
    from .cache import get_cache
except ImportError:
    from cache import get_cache

# Cache configuration
CACHE_EXPIRY_HOURS_ODDS = 6      # Odds change frequently
CACHE_EXPIRY_HOURS_FIXTURES = 24  # Fixtures are more stable
CACHE_EXPIRY_HOURS_STANDINGS = 24

# API Configuration
API_FOOTBALL_BASE_URL = "https://v3.football.api-sports.io"
API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY', None)

# Bundesliga League ID in API-Football
BUNDESLIGA_LEAGUE_ID = 78

# Bookmaker IDs in API-Football
BOOKMAKERS = {
    'pinnacle': 11,      # Pinnacle (lowest margin, professional)
    'betfair': 3,        # Betfair Exchange (fair odds, no bookmaker margin)
    'bet365': 8          # Bet365 (popular, good coverage)
}


class APIFootballClient:
    """
    Client for API-Football (RapidAPI)
    Provides odds, fixtures, standings, and team statistics
    """

    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True):
        """
        Initialize API-Football client

        Args:
            api_key: API-Football API key (get from RapidAPI)
            use_cache: If True, use file cache to reduce API calls
        """
        self.api_key = api_key or API_FOOTBALL_KEY
        self.use_cache = use_cache
        self.cache = get_cache() if use_cache else None

        # Set up session with headers
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'x-rapidapi-host': 'v3.football.api-sports.io',
                'x-rapidapi-key': self.api_key
            })

        self.mock_mode = not self.api_key

    def _make_request(self, endpoint: str, params: Dict) -> Optional[Dict]:
        """
        Make API request with error handling

        Args:
            endpoint: API endpoint (e.g., '/odds')
            params: Query parameters

        Returns:
            Response JSON or None on error
        """
        if self.mock_mode:
            return None  # Mock data will be generated in calling functions

        url = f"{API_FOOTBALL_BASE_URL}{endpoint}"

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Check API response structure
            if data.get('errors') and len(data['errors']) > 0:
                print(f"⚠️  API Error: {data['errors']}")
                return None

            return data

        except requests.exceptions.RequestException as e:
            print(f"✗ API Request failed: {e}")
            return None
        except Exception as e:
            print(f"✗ Error processing API response: {e}")
            return None

    def _normalize_team_name(self, team_name: str) -> str:
        """
        Normalize team name for matching

        Args:
            team_name: Team name from any source

        Returns:
            Normalized team name
        """
        replacements = {
            'FC Bayern München': 'Bayern München',
            'FC Bayern Munchen': 'Bayern München',
            'Bayern Munich': 'Bayern München',
            'Bayer 04 Leverkusen': 'Bayer Leverkusen',
            'RasenBallsport Leipzig': 'RB Leipzig',
            '1. FC Union Berlin': 'Union Berlin',
            'Sport-Club Freiburg': 'SC Freiburg',
            '1. FSV Mainz 05': 'Mainz 05',
            "Borussia M'gladbach": 'Borussia Mönchengladbach',
            'Borussia Monchengladbach': 'Borussia Mönchengladbach',
            '1. FC Köln': 'FC Köln',
            'TSG 1899 Hoffenheim': 'TSG Hoffenheim',
            'SV Werder Bremen': 'Werder Bremen',
            'VfL Bochum 1848': 'VfL Bochum',
            '1. FC Heidenheim 1846': 'FC Heidenheim',
        }

        normalized = team_name
        for old, new in replacements.items():
            if old.lower() in team_name.lower():
                normalized = new
                break

        return normalized

    def find_fixture_id(self, home_team: str, away_team: str, season: int = 2024) -> Optional[int]:
        """
        Find fixture ID for a match between two teams

        Args:
            home_team: Home team name
            away_team: Away team name
            season: Season year

        Returns:
            Fixture ID or None
        """
        # Check cache first
        cache_key = f"fixture_id_{home_team}_{away_team}_{season}"
        if self.use_cache and self.cache:
            cached_id = self.cache.get(cache_key, expiry_hours=CACHE_EXPIRY_HOURS_FIXTURES)
            if cached_id:
                return cached_id

        # Get all fixtures for the season
        fixtures = self.get_bundesliga_fixtures(season=season)

        if fixtures is None or fixtures.empty:
            return None

        # Normalize team names
        home_normalized = self._normalize_team_name(home_team)
        away_normalized = self._normalize_team_name(away_team)

        # Find matching fixture
        for _, fixture in fixtures.iterrows():
            fixture_home = self._normalize_team_name(str(fixture.get('HomeTeam', '')))
            fixture_away = self._normalize_team_name(str(fixture.get('AwayTeam', '')))

            if (home_normalized.lower() in fixture_home.lower() and
                away_normalized.lower() in fixture_away.lower()):
                fixture_id = fixture.get('fixture_id')

                # Cache the result
                if self.use_cache and self.cache and fixture_id:
                    self.cache.set(cache_key, fixture_id)

                return fixture_id

        print(f"⚠️  No fixture found for {home_team} vs {away_team}")
        return None

    def get_match_odds(self, home_team: str, away_team: str, season: int = 2024) -> Optional[Dict]:
        """
        Get betting odds for a match from multiple bookmakers

        Args:
            home_team: Home team name
            away_team: Away team name
            season: Season year

        Returns:
            Dictionary with odds from Pinnacle, Betfair, and Bet365
        """
        # Check cache first
        cache_key = f"odds_{home_team}_{away_team}_{season}"
        if self.use_cache and self.cache:
            cached_odds = self.cache.get(cache_key, expiry_hours=CACHE_EXPIRY_HOURS_ODDS)
            if cached_odds:
                print(f"✓ Using cached odds for {home_team} vs {away_team}")
                return cached_odds

        # Find fixture ID
        fixture_id = self.find_fixture_id(home_team, away_team, season)

        if not fixture_id:
            if self.mock_mode:
                print(f"⚠️  Mock mode: Generating sample odds for {home_team} vs {away_team}")
                return self._generate_mock_odds(home_team, away_team)
            return None

        # Fetch odds from API
        # Note: We fetch all bookmakers and filter afterwards
        # API-Football doesn't support multiple bookmaker IDs in one request
        params = {
            'fixture': fixture_id
        }

        response = self._make_request('/odds', params)

        if not response or not response.get('response'):
            print(f"⚠️  No odds data available from API")
            return self._generate_mock_odds(home_team, away_team)

        # Parse odds
        odds_data = self._parse_odds_response(response['response'], home_team, away_team)

        # Cache the result
        if self.use_cache and self.cache and odds_data:
            self.cache.set(cache_key, odds_data)

        return odds_data

    def _parse_odds_response(self, response: List[Dict], home_team: str, away_team: str) -> Dict:
        """
        Parse odds from API response

        Args:
            response: API response with odds data
            home_team: Home team name
            away_team: Away team name

        Returns:
            Structured odds dictionary
        """
        result = {
            'home_team': home_team,
            'away_team': away_team,
            'pinnacle': None,
            'betfair': None,
            'bet365': None,
            'best_odds': None,
            'fair_odds': None,
            'timestamp': datetime.now().isoformat()
        }

        if not response:
            return result

        # Process each bookmaker
        for odds_entry in response:
            bookmaker_name = odds_entry.get('bookmaker', {}).get('name', '').lower()

            # Find Match Winner market (1X2)
            for bet in odds_entry.get('bets', []):
                if bet.get('name') == 'Match Winner':
                    values = bet.get('values', [])

                    odds_dict = {}
                    for val in values:
                        label = val.get('value')
                        odd = float(val.get('odd', 0))

                        if label == 'Home':
                            odds_dict['home'] = odd
                        elif label == 'Draw':
                            odds_dict['draw'] = odd
                        elif label == 'Away':
                            odds_dict['away'] = odd

                    # Store by bookmaker
                    if 'pinnacle' in bookmaker_name:
                        result['pinnacle'] = odds_dict
                    elif 'betfair' in bookmaker_name:
                        result['betfair'] = odds_dict
                        # Betfair Exchange has no margin - use as "fair odds"
                        result['fair_odds'] = odds_dict
                    elif 'bet365' in bookmaker_name:
                        result['bet365'] = odds_dict

        # Calculate best odds (highest from any bookmaker)
        result['best_odds'] = self._calculate_best_odds(result)

        return result

    def _calculate_best_odds(self, odds_data: Dict) -> Optional[Dict]:
        """
        Calculate best available odds across all bookmakers

        Args:
            odds_data: Dictionary with odds from different bookmakers

        Returns:
            Dictionary with best odds for each outcome
        """
        best = {'home': 0, 'draw': 0, 'away': 0}

        for bookmaker in ['pinnacle', 'betfair', 'bet365']:
            odds = odds_data.get(bookmaker)
            if odds:
                if odds.get('home', 0) > best['home']:
                    best['home'] = odds['home']
                if odds.get('draw', 0) > best['draw']:
                    best['draw'] = odds['draw']
                if odds.get('away', 0) > best['away']:
                    best['away'] = odds['away']

        return best if best['home'] > 0 else None

    def _generate_mock_odds(self, home_team: str, away_team: str) -> Dict:
        """
        Generate realistic mock odds for testing

        Args:
            home_team: Home team name
            away_team: Away team name

        Returns:
            Mock odds dictionary
        """
        # Simple team strength estimation
        top_teams = ['Bayern München', 'Borussia Dortmund', 'Bayer Leverkusen', 'RB Leipzig']
        mid_teams = ['VfB Stuttgart', 'Eintracht Frankfurt', 'VfL Wolfsburg', 'SC Freiburg']

        home_norm = self._normalize_team_name(home_team)
        away_norm = self._normalize_team_name(away_team)

        # Determine odds based on team strength
        if home_norm in top_teams and away_norm not in top_teams + mid_teams:
            base_odds = {'home': 1.50, 'draw': 4.50, 'away': 7.00}
        elif away_norm in top_teams and home_norm not in top_teams + mid_teams:
            base_odds = {'home': 6.00, 'draw': 4.50, 'away': 1.60}
        elif home_norm in top_teams and away_norm in top_teams:
            base_odds = {'home': 2.20, 'draw': 3.50, 'away': 3.00}
        else:
            base_odds = {'home': 2.50, 'draw': 3.40, 'away': 2.80}

        # Add slight variations for different bookmakers
        return {
            'home_team': home_team,
            'away_team': away_team,
            'pinnacle': {
                'home': base_odds['home'],
                'draw': base_odds['draw'],
                'away': base_odds['away']
            },
            'betfair': {
                'home': base_odds['home'] * 1.02,  # Slightly worse
                'draw': base_odds['draw'] * 0.98,
                'away': base_odds['away'] * 1.01
            },
            'bet365': {
                'home': base_odds['home'] * 0.98,  # Slightly better
                'draw': base_odds['draw'] * 0.97,
                'away': base_odds['away'] * 0.99
            },
            'best_odds': base_odds,
            'fair_odds': base_odds,  # Use Betfair as fair
            'timestamp': datetime.now().isoformat(),
            'source': 'mock'
        }

    def get_bundesliga_fixtures(self, season: int = 2024, matchday: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Get Bundesliga fixtures for a season

        Args:
            season: Season year (e.g., 2024 for 2024/2025 season)
            matchday: Optional specific matchday

        Returns:
            DataFrame with fixtures
        """
        # Check cache
        cache_key = f"fixtures_bundesliga_{season}_{matchday or 'all'}"
        if self.use_cache and self.cache:
            cached_fixtures = self.cache.get(cache_key, expiry_hours=CACHE_EXPIRY_HOURS_FIXTURES)
            if cached_fixtures is not None:
                print(f"✓ Using cached fixtures for season {season}")
                return cached_fixtures

        params = {
            'league': BUNDESLIGA_LEAGUE_ID,
            'season': season
        }

        if matchday:
            params['round'] = f'Regular Season - {matchday}'

        response = self._make_request('/fixtures', params)

        if not response or not response.get('response'):
            print(f"⚠️  No fixtures data from API")
            return None

        # Parse fixtures
        fixtures = []
        for fixture in response['response']:
            fixtures.append({
                'fixture_id': fixture['fixture']['id'],
                'Date': fixture['fixture']['date'],
                'Matchday': fixture['league'].get('round', '').replace('Regular Season - ', ''),
                'HomeTeam': fixture['teams']['home']['name'],
                'AwayTeam': fixture['teams']['away']['name'],
                'HomeGoals': fixture['goals']['home'],
                'AwayGoals': fixture['goals']['away'],
                'Status': fixture['fixture']['status']['short'],
                'Venue': fixture['fixture']['venue']['name'],
                'Referee': fixture['fixture']['referee']
            })

        df = pd.DataFrame(fixtures)

        # Cache the result
        if self.use_cache and self.cache and not df.empty:
            self.cache.set(cache_key, df)

        return df

    def get_bundesliga_standings(self, season: int = 2024) -> Optional[pd.DataFrame]:
        """
        Get Bundesliga standings/table

        Args:
            season: Season year

        Returns:
            DataFrame with standings
        """
        # Check cache
        cache_key = f"standings_bundesliga_{season}"
        if self.use_cache and self.cache:
            cached_standings = self.cache.get(cache_key, expiry_hours=CACHE_EXPIRY_HOURS_STANDINGS)
            if cached_standings is not None:
                print(f"✓ Using cached standings for season {season}")
                return cached_standings

        params = {
            'league': BUNDESLIGA_LEAGUE_ID,
            'season': season
        }

        response = self._make_request('/standings', params)

        if not response or not response.get('response'):
            print(f"⚠️  No standings data from API")
            return None

        # Parse standings
        standings = []
        for league in response['response']:
            for standing in league['league']['standings'][0]:  # [0] is overall standings
                standings.append({
                    'Rank': standing['rank'],
                    'Team': standing['team']['name'],
                    'Played': standing['all']['played'],
                    'Won': standing['all']['win'],
                    'Draw': standing['all']['draw'],
                    'Lost': standing['all']['lose'],
                    'GoalsFor': standing['all']['goals']['for'],
                    'GoalsAgainst': standing['all']['goals']['against'],
                    'GoalDifference': standing['goalsDiff'],
                    'Points': standing['points'],
                    'Form': standing['form']
                })

        df = pd.DataFrame(standings)

        # Cache the result
        if self.use_cache and self.cache and not df.empty:
            self.cache.set(cache_key, df)

        return df

    def check_xg_availability(self, season: int = 2024) -> bool:
        """
        Check if xG data is available for Bundesliga

        Args:
            season: Season year

        Returns:
            True if xG data is available
        """
        print(f"🔍 Checking xG data availability for Bundesliga {season}...")

        # Get a sample fixture
        fixtures = self.get_bundesliga_fixtures(season=season)

        if fixtures is None or fixtures.empty:
            print("⚠️  No fixtures available to check xG")
            return False

        # Get first completed match
        completed = fixtures[fixtures['Status'] == 'FT'].head(1)

        if completed.empty:
            print("⚠️  No completed matches to check xG")
            return False

        fixture_id = completed.iloc[0]['fixture_id']

        # Check fixture statistics
        params = {'fixture': fixture_id}
        response = self._make_request('/fixtures/statistics', params)

        if not response or not response.get('response'):
            print("✗ No statistics data available")
            return False

        # Look for xG in statistics
        for team_stats in response['response']:
            stats = team_stats.get('statistics', [])
            for stat in stats:
                if 'xG' in stat.get('type', '') or 'expected' in stat.get('type', '').lower():
                    print(f"✓ xG data IS available for Bundesliga!")
                    print(f"  Found: {stat.get('type')} = {stat.get('value')}")
                    return True

        print("✗ xG data NOT available for Bundesliga in API-Football")
        return False

    def get_match_xg(self, home_team: str, away_team: str, season: int = 2024) -> Optional[Dict]:
        """
        Get xG data for a specific match

        Args:
            home_team: Home team name
            away_team: Away team name
            season: Season year

        Returns:
            Dictionary with xG data for both teams
        """
        # Find fixture ID
        fixture_id = self.find_fixture_id(home_team, away_team, season)

        if not fixture_id:
            return None

        # Check cache
        cache_key = f"xg_{fixture_id}"
        if self.use_cache and self.cache:
            cached_xg = self.cache.get(cache_key, expiry_hours=CACHE_EXPIRY_HOURS_FIXTURES)
            if cached_xg:
                return cached_xg

        # Fetch statistics
        params = {'fixture': fixture_id}
        response = self._make_request('/fixtures/statistics', params)

        if not response or not response.get('response'):
            return None

        # Parse xG data
        result = {
            'home_team': home_team,
            'away_team': away_team,
            'home_xg': None,
            'away_xg': None
        }

        for idx, team_stats in enumerate(response['response']):
            stats = team_stats.get('statistics', [])
            for stat in stats:
                stat_type = stat.get('type', '')
                stat_value = stat.get('value')

                if 'expected_goals' in stat_type.lower() or stat_type == 'expected_goals':
                    if idx == 0:  # First team is home
                        result['home_xg'] = float(stat_value) if stat_value else None
                    else:  # Second team is away
                        result['away_xg'] = float(stat_value) if stat_value else None

        # Cache the result
        if self.use_cache and self.cache:
            self.cache.set(cache_key, result)

        return result

    def get_team_xg_stats(self, season: int = 2024) -> Optional[pd.DataFrame]:
        """
        Get xG statistics for all Bundesliga teams in a season

        Args:
            season: Season year

        Returns:
            DataFrame with team xG statistics
        """
        # Check cache
        cache_key = f"team_xg_stats_{season}"
        if self.use_cache and self.cache:
            cached_stats = self.cache.get(cache_key, expiry_hours=CACHE_EXPIRY_HOURS_FIXTURES)
            if cached_stats is not None:
                print(f"✓ Using cached team xG stats for season {season}")
                return cached_stats

        # Get all completed fixtures
        fixtures = self.get_bundesliga_fixtures(season=season)

        if fixtures is None or fixtures.empty:
            return None

        completed = fixtures[fixtures['Status'] == 'FT']

        if completed.empty:
            print("⚠️  No completed matches for xG statistics")
            return None

        print(f"📊 Calculating xG statistics from {len(completed)} matches...")

        # Aggregate xG stats per team
        team_stats = {}

        for _, fixture in completed.iterrows():
            fixture_id = fixture['fixture_id']
            home_team = fixture['HomeTeam']
            away_team = fixture['AwayTeam']

            # Get match statistics
            params = {'fixture': fixture_id}
            response = self._make_request('/fixtures/statistics', params)

            if not response or not response.get('response'):
                continue

            # Parse xG for both teams
            for idx, team_stats_data in enumerate(response['response']):
                team_name = home_team if idx == 0 else away_team
                is_home = idx == 0

                # Initialize team stats if needed
                if team_name not in team_stats:
                    team_stats[team_name] = {
                        'Team': team_name,
                        'xG_for': [],
                        'xG_against': [],
                        'matches': 0
                    }

                # Extract xG
                stats = team_stats_data.get('statistics', [])
                for stat in stats:
                    if 'expected_goals' in stat.get('type', '').lower():
                        xg_value = float(stat.get('value', 0)) if stat.get('value') else 0

                        # Add to xG for
                        team_stats[team_name]['xG_for'].append(xg_value)

                        # Add to opponent's xG against
                        opponent = away_team if is_home else home_team
                        if opponent not in team_stats:
                            team_stats[opponent] = {
                                'Team': opponent,
                                'xG_for': [],
                                'xG_against': [],
                                'matches': 0
                            }
                        team_stats[opponent]['xG_against'].append(xg_value)

                team_stats[team_name]['matches'] += 1

        # Calculate averages
        results = []
        for team, data in team_stats.items():
            matches = data['matches']
            if matches > 0:
                avg_xg_for = sum(data['xG_for']) / len(data['xG_for']) if data['xG_for'] else 0
                avg_xg_against = sum(data['xG_against']) / len(data['xG_against']) if data['xG_against'] else 0

                results.append({
                    'Team': team,
                    'Matches': matches,
                    'xG_For': round(avg_xg_for, 2),
                    'xG_Against': round(avg_xg_against, 2),
                    'xG_Diff': round(avg_xg_for - avg_xg_against, 2)
                })

        df = pd.DataFrame(results)

        if not df.empty:
            df = df.sort_values('xG_For', ascending=False)
            df.reset_index(drop=True, inplace=True)

        # Cache the result
        if self.use_cache and self.cache and not df.empty:
            self.cache.set(cache_key, df)

        print(f"✓ Calculated xG stats for {len(df)} teams")

        return df


def main():
    """Test API-Football client"""

    print("=" * 80)
    print("API-Football Client - Test")
    print("=" * 80)

    client = APIFootballClient()

    if client.mock_mode:
        print("\n⚠️  Running in MOCK MODE (no API key)")
        print("Set API_FOOTBALL_KEY environment variable for real data\n")

    # Test 1: Get odds
    print("\n1. Testing Odds (Pinnacle, Betfair, Bet365):")
    print("-" * 80)
    odds = client.get_match_odds("Bayern München", "VfL Bochum")

    if odds:
        print(f"\nMatch: {odds['home_team']} vs {odds['away_team']}")

        for bookmaker in ['pinnacle', 'betfair', 'bet365']:
            bm_odds = odds.get(bookmaker)
            if bm_odds:
                print(f"\n{bookmaker.capitalize()}:")
                print(f"  Home: {bm_odds.get('home', 'N/A')}")
                print(f"  Draw: {bm_odds.get('draw', 'N/A')}")
                print(f"  Away: {bm_odds.get('away', 'N/A')}")

        if odds.get('best_odds'):
            print(f"\nBest Available Odds:")
            print(f"  Home: {odds['best_odds']['home']}")
            print(f"  Draw: {odds['best_odds']['draw']}")
            print(f"  Away: {odds['best_odds']['away']}")

    # Test 2: Check xG availability
    print("\n\n2. Checking xG Data Availability:")
    print("-" * 80)
    has_xg = client.check_xg_availability(2024)
    print(f"Result: {'✓ Available' if has_xg else '✗ Not Available'}")

    # Test 3: Get standings (if not in mock mode)
    if not client.mock_mode:
        print("\n\n3. Testing Bundesliga Standings:")
        print("-" * 80)
        standings = client.get_bundesliga_standings(2024)
        if standings is not None and not standings.empty:
            print(standings.head(5).to_string(index=False))

    print("\n" + "=" * 80)
    print("API-Football Client Test Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
