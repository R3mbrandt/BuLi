"""
Transfermarkt Web Scraper
Scrapes squad values and injury data from Transfermarkt.de

Website: https://www.transfermarkt.de/
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from typing import Optional, Dict, List
from urllib.parse import quote


# Modern Chrome User-Agent (January 2025)
MODERN_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'


class TransfermarktScraper:
    """
    Scrapes data from Transfermarkt.de
    - Squad values (monetary team value)
    - Injury data (number and details of injured players)
    """

    BASE_URL = "https://www.transfermarkt.de"

    # Known Bundesliga team mappings (Transfermarkt URLs and IDs)
    TEAM_MAPPINGS = {
        # Format: 'Team Name': ('url-slug', verein_id)
        # Full names as they appear in OpenLigaDB
        'Bayern München': ('fc-bayern-munchen', 27),
        'FC Bayern München': ('fc-bayern-munchen', 27),
        'Borussia Dortmund': ('borussia-dortmund', 16),
        'RB Leipzig': ('rasenballsport-leipzig', 23826),
        'Bayer Leverkusen': ('bayer-04-leverkusen', 15),
        'Bayer 04 Leverkusen': ('bayer-04-leverkusen', 15),
        'Union Berlin': ('1-fc-union-berlin', 89),
        '1. FC Union Berlin': ('1-fc-union-berlin', 89),
        'SC Freiburg': ('sc-freiburg', 60),
        'Sport-Club Freiburg': ('sc-freiburg', 60),
        'Eintracht Frankfurt': ('eintracht-frankfurt', 24),
        'VfL Wolfsburg': ('vfl-wolfsburg', 82),
        'Mainz 05': ('1-fsv-mainz-05', 39),
        '1. FSV Mainz 05': ('1-fsv-mainz-05', 39),
        'FSV Mainz 05': ('1-fsv-mainz-05', 39),
        'Borussia Mönchengladbach': ('borussia-monchengladbach', 18),
        "Borussia M'gladbach": ('borussia-monchengladbach', 18),
        '1. FC Köln': ('1-fc-koln', 3),
        'FC Köln': ('1-fc-koln', 3),
        'TSG Hoffenheim': ('tsg-1899-hoffenheim', 533),
        'TSG 1899 Hoffenheim': ('tsg-1899-hoffenheim', 533),
        'VfB Stuttgart': ('vfb-stuttgart', 79),
        'Werder Bremen': ('sv-werder-bremen', 86),
        'SV Werder Bremen': ('sv-werder-bremen', 86),
        'VfL Bochum': ('vfl-bochum', 80),
        'VfL Bochum 1848': ('vfl-bochum', 80),
        'FC Augsburg': ('fc-augsburg', 167),
        'FC Heidenheim': ('1-fc-heidenheim-1846', 2036),
        '1. FC Heidenheim': ('1-fc-heidenheim-1846', 2036),
        '1. FC Heidenheim 1846': ('1-fc-heidenheim-1846', 2036),
        'SV Darmstadt 98': ('sv-darmstadt-98', 105),
        'Holstein Kiel': ('holstein-kiel', 1128),
        'FC St. Pauli': ('fc-st-pauli', 35)
    }

    def __init__(self):
        """Initialize Transfermarkt scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': MODERN_USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })

    def _get_team_info(self, team_name: str) -> Optional[tuple]:
        """
        Get Transfermarkt URL slug and verein ID for a team

        Args:
            team_name: Team name (can be partial)

        Returns:
            Tuple of (url_slug, verein_id) or None if not found
        """
        # Try exact match first
        if team_name in self.TEAM_MAPPINGS:
            return self.TEAM_MAPPINGS[team_name]

        # Try partial match
        for full_name, info in self.TEAM_MAPPINGS.items():
            if team_name.lower() in full_name.lower():
                return info

        return None

    def _parse_value_string(self, value_str: str) -> float:
        """
        Parse Transfermarkt value string to float

        Examples:
            "€50.00m" -> 50_000_000
            "€1.50bn" -> 1_500_000_000
            "€500.00k" -> 500_000

        Args:
            value_str: Value string from Transfermarkt

        Returns:
            Value as float in EUR
        """
        if not value_str or value_str == '-':
            return 0.0

        # Remove currency symbol and whitespace
        value_str = value_str.replace('€', '').replace(' ', '').strip()

        # Extract number and unit
        match = re.match(r'([\d,.]+)([a-zA-Z]*)', value_str)
        if not match:
            return 0.0

        number_str, unit = match.groups()

        # Convert number (handle both comma and dot as decimal separator)
        number_str = number_str.replace(',', '.')
        try:
            number = float(number_str)
        except ValueError:
            return 0.0

        # Apply multiplier based on unit
        unit = unit.lower()
        if unit == 'bn' or unit == 'mrd':  # billion / Milliarde
            return number * 1_000_000_000
        elif unit == 'm' or unit == 'mio':  # million
            return number * 1_000_000
        elif unit == 'k' or unit == 'tsd':  # thousand / Tausend
            return number * 1_000
        else:
            return number

    def get_squad_value(self, team_name: str) -> Optional[Dict]:
        """
        Get squad value for a team

        Args:
            team_name: Team name

        Returns:
            Dictionary with squad value info or None
        """
        team_info = self._get_team_info(team_name)
        if not team_info:
            print(f"⚠️  Team '{team_name}' not found in Transfermarkt mappings")
            return None

        team_slug, verein_id = team_info

        # Transfermarkt squad overview URL with correct verein ID
        url = f"{self.BASE_URL}/{team_slug}/kader/verein/{verein_id}/saison_id/2024"

        try:
            print(f"Fetching squad value for {team_name}...")
            time.sleep(2)  # Be respectful to the server

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Find squad value in the page
            # Transfermarkt shows it in a specific box
            value_box = soup.find('div', class_='box')
            if not value_box:
                print(f"Could not find value box for {team_name}")
                return None

            # Look for the total value
            value_elements = soup.find_all('a', class_='data-header__market-value-wrapper')
            if not value_elements:
                # Try alternative selector
                value_elements = soup.find_all(text=re.compile(r'Gesamtmarktwert:'))

            total_value = 0.0
            for elem in value_elements:
                # Get the value text
                if hasattr(elem, 'text'):
                    value_text = elem.text
                else:
                    value_text = str(elem)

                # Extract value
                if '€' in value_text:
                    value_match = re.search(r'€[\d,.]+(Mio\.|Mrd\.)?', value_text)
                    if value_match:
                        value_str = value_match.group(0)
                        total_value = self._parse_value_string(value_str)
                        break

            # Alternative: Sum up individual player values
            if total_value == 0.0:
                player_values = soup.find_all('td', class_='rechts hauptlink')
                for pv in player_values:
                    a_tag = pv.find('a')
                    if a_tag and '€' in a_tag.text:
                        value = self._parse_value_string(a_tag.text)
                        total_value += value

            if total_value > 0:
                print(f"✓ Found squad value: €{total_value:,.0f}")
                return {
                    'team': team_name,
                    'squad_value': total_value,
                    'squad_value_millions': total_value / 1_000_000,
                    'source': 'transfermarkt',
                    'url': url
                }
            else:
                print(f"⚠️  Could not extract squad value for {team_name}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching squad value for {team_name}: {e}")
            return None
        except Exception as e:
            print(f"✗ Error parsing squad value for {team_name}: {e}")
            return None

    def get_all_bundesliga_squad_values(self) -> pd.DataFrame:
        """
        Get squad values for all Bundesliga teams

        Returns:
            DataFrame with squad values
        """
        results = []

        print("\n" + "=" * 70)
        print("Fetching Bundesliga Squad Values from Transfermarkt")
        print("=" * 70)

        for team_name in self.TEAM_MAPPINGS.keys():
            data = self.get_squad_value(team_name)
            if data:
                results.append(data)
            time.sleep(2)  # Rate limiting

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('squad_value', ascending=False)
            df.reset_index(drop=True, inplace=True)
            df.insert(0, 'rank', range(1, len(df) + 1))

        return df

    def get_injuries(self, team_name: str) -> Optional[Dict]:
        """
        Get injury information for a team

        Args:
            team_name: Team name

        Returns:
            Dictionary with injury info or None
        """
        team_info = self._get_team_info(team_name)
        if not team_info:
            print(f"⚠️  Team '{team_name}' not found in Transfermarkt mappings")
            return None

        team_slug, verein_id = team_info

        # Transfermarkt injury page URL
        url = f"{self.BASE_URL}/{team_slug}/verletztespieler/verein/{verein_id}"

        try:
            print(f"Fetching injuries for {team_name}...")
            time.sleep(2)  # Be respectful to the server

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')

            # Find all injured players
            # Transfermarkt shows injuries in a specific table
            injury_table = soup.find('table', class_='items')

            if not injury_table:
                print(f"No injury table found for {team_name}")
                return {
                    'team': team_name,
                    'injured_count': 0,
                    'injured_players': [],
                    'source': 'transfermarkt',
                    'url': url
                }

            # Parse injury rows
            injured_players = []
            rows = injury_table.find_all('tr', class_=['odd', 'even'])

            for row in rows:
                try:
                    # Get player name
                    player_cell = row.find('td', class_='hauptlink')
                    if not player_cell:
                        continue

                    player_link = player_cell.find('a')
                    player_name = player_link.text.strip() if player_link else 'Unknown'

                    # Get injury type
                    injury_cell = row.find_all('td')
                    injury_type = 'Unknown'
                    expected_return = 'Unknown'

                    # Try to extract injury details
                    if len(injury_cell) >= 4:
                        # Injury type is usually in a specific column
                        for cell in injury_cell:
                            cell_text = cell.text.strip()
                            if cell_text and not cell_text.isdigit() and cell_text != player_name:
                                if not injury_type or injury_type == 'Unknown':
                                    injury_type = cell_text
                                elif not expected_return or expected_return == 'Unknown':
                                    expected_return = cell_text

                    injured_players.append({
                        'name': player_name,
                        'injury': injury_type,
                        'expected_return': expected_return
                    })

                except Exception as e:
                    # Skip this row if parsing fails
                    continue

            print(f"✓ Found {len(injured_players)} injured player(s)")

            return {
                'team': team_name,
                'injured_count': len(injured_players),
                'injured_players': injured_players,
                'source': 'transfermarkt',
                'url': url
            }

        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching injuries for {team_name}: {e}")
            return None
        except Exception as e:
            print(f"✗ Error parsing injuries for {team_name}: {e}")
            return None

    def get_all_bundesliga_injuries(self) -> pd.DataFrame:
        """
        Get injury data for all Bundesliga teams

        Returns:
            DataFrame with injury counts
        """
        results = []

        print("\n" + "=" * 70)
        print("Fetching Bundesliga Injuries from Transfermarkt")
        print("=" * 70)

        for team_name in self.TEAM_MAPPINGS.keys():
            # Skip duplicates (we have multiple names for same team)
            if any(r['team'] == team_name for r in results):
                continue

            data = self.get_injuries(team_name)
            if data:
                results.append({
                    'team': data['team'],
                    'injured_count': data['injured_count'],
                    'players': ', '.join([p['name'] for p in data['injured_players'][:3]])  # First 3
                })
            time.sleep(2)  # Rate limiting

        df = pd.DataFrame(results)
        if not df.empty:
            df = df.sort_values('injured_count', ascending=False)
            df.reset_index(drop=True, inplace=True)

        return df


def get_squad_value_with_fallback(team_name: str, fallback_data: Optional[Dict] = None) -> Dict:
    """
    Get squad value with automatic fallback to mock data

    Args:
        team_name: Team name
        fallback_data: Optional dict with fallback values (from mock_data.py)

    Returns:
        Dictionary with squad value
    """
    scraper = TransfermarktScraper()
    data = scraper.get_squad_value(team_name)

    if data:
        return data

    # Fallback to mock data
    if fallback_data and team_name in fallback_data:
        print(f"ℹ️  Using fallback data for {team_name}")
        return {
            'team': team_name,
            'squad_value': fallback_data[team_name]['squad_value'],
            'squad_value_millions': fallback_data[team_name]['squad_value'] / 1_000_000,
            'source': 'mock',
            'url': None
        }

    # Ultimate fallback: default value
    print(f"⚠️  Using default value for {team_name}")
    return {
        'team': team_name,
        'squad_value': 100_000_000,  # 100M default
        'squad_value_millions': 100.0,
        'source': 'default',
        'url': None
    }


def get_injuries_with_fallback(team_name: str, fallback_data: Optional[Dict] = None) -> Dict:
    """
    Get injury data with automatic fallback to mock data

    Args:
        team_name: Team name
        fallback_data: Optional dict with fallback values

    Returns:
        Dictionary with injury data
    """
    scraper = TransfermarktScraper()
    data = scraper.get_injuries(team_name)

    if data:
        return data

    # Fallback to mock data
    if fallback_data and team_name in fallback_data:
        print(f"ℹ️  Using fallback injury data for {team_name}")
        return {
            'team': team_name,
            'injured_count': fallback_data[team_name].get('injuries', 2),
            'injured_players': [],
            'source': 'mock',
            'url': None
        }

    # Ultimate fallback: default value
    print(f"⚠️  Using default injury count for {team_name}")
    return {
        'team': team_name,
        'injured_count': 2,  # Default
        'injured_players': [],
        'source': 'default',
        'url': None
    }


def main():
    """Test Transfermarkt scraper"""

    print("=" * 70)
    print("Transfermarkt Scraper Test - Squad Values & Injuries")
    print("=" * 70)

    scraper = TransfermarktScraper()

    # Test 1: Get single team value
    print("\n1. Testing squad value (Bayern München):")
    print("-" * 70)
    bayern_data = scraper.get_squad_value("Bayern München")

    if bayern_data:
        print("\nResult:")
        print(f"  Team: {bayern_data['team']}")
        print(f"  Squad Value: €{bayern_data['squad_value']:,.0f}")
        print(f"  Squad Value: €{bayern_data['squad_value_millions']:.1f}M")
        print(f"  URL: {bayern_data['url']}")
    else:
        print("Failed to fetch data")

    # Test 2: Get injuries
    print("\n\n2. Testing injuries (Bayern München):")
    print("-" * 70)
    bayern_injuries = scraper.get_injuries("Bayern München")

    if bayern_injuries:
        print("\nResult:")
        print(f"  Team: {bayern_injuries['team']}")
        print(f"  Injured Count: {bayern_injuries['injured_count']}")
        if bayern_injuries['injured_players']:
            print(f"  Injured Players:")
            for player in bayern_injuries['injured_players'][:5]:  # Show first 5
                print(f"    - {player['name']}: {player['injury']}")
    else:
        print("Failed to fetch injury data")

    # Test 3: Test multiple teams
    print("\n\n3. Testing multiple teams (Squad Values):")
    print("-" * 70)

    test_teams = ['Bayern München', 'VfB Stuttgart', '1. FSV Mainz 05']

    for team in test_teams:
        value_data = scraper.get_squad_value(team)
        injury_data = scraper.get_injuries(team)

        if value_data and injury_data:
            print(f"\n{team}:")
            print(f"  Value: €{value_data['squad_value_millions']:.1f}M")
            print(f"  Injuries: {injury_data['injured_count']}")

    print("\n" + "=" * 70)
    print("Transfermarkt Scraper Test Completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
