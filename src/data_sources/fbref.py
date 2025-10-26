"""
FBref Data Integration
Scrapes Bundesliga data from FBref.com including:
- League table/standings
- Match results
- xG (Expected Goals) data
- Team statistics

Uses CloudScraper to bypass Cloudflare protection
"""

import cloudscraper
import requests  # For exception handling
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import time
import re


class FBrefScraper:
    """
    Scrapes Bundesliga data from FBref.com
    Website: https://fbref.com/
    """

    BASE_URL = "https://fbref.com"
    BUNDESLIGA_URL = "https://fbref.com/en/comps/20"

    # Competition ID for Bundesliga
    BUNDESLIGA_ID = "20"

    def __init__(self):
        # Use cloudscraper to bypass Cloudflare protection
        # Note: This works on local machines but may be blocked in cloud/datacenter environments
        # FBref blocks datacenter IPs but allows residential IPs
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        # CloudScraper handles headers automatically, but we can add custom ones
        self.session.headers.update({
            'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        })

    def _get_page(self, url: str, delay: float = 3.0) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return BeautifulSoup object

        Args:
            url: URL to fetch
            delay: Delay between requests (be nice to the server)

        Returns:
            BeautifulSoup object or None if error
        """
        try:
            time.sleep(delay)  # Be nice to the server
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'lxml')
            return soup

        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_league_table(self, season: str = "2024-2025") -> pd.DataFrame:
        """
        Get current Bundesliga league table/standings

        Args:
            season: Season in format "YYYY-YYYY" (e.g., "2024-2025")

        Returns:
            DataFrame with league table
        """
        url = f"{self.BUNDESLIGA_URL}/Bundesliga-Stats"
        soup = self._get_page(url)

        if not soup:
            return pd.DataFrame()

        try:
            # Find the league table
            # FBref uses specific table IDs
            table = soup.find('table', {'id': 'results2024-202520_overall'})

            if not table:
                # Try to find any table with "overall" standings
                table = soup.find('table', class_='stats_table')

            if not table:
                print("Could not find league table")
                return pd.DataFrame()

            # Parse table using pandas
            df = pd.read_html(str(table))[0]

            # Clean up multi-level columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns.values]

            # Rename common columns
            column_mapping = {
                'Rk': 'Rank',
                'Squad': 'Team',
                'MP': 'Played',
                'W': 'Won',
                'D': 'Draw',
                'L': 'Lost',
                'GF': 'GoalsFor',
                'GA': 'GoalsAgainst',
                'GD': 'GoalDifference',
                'Pts': 'Points',
                'xG': 'xG',
                'xGA': 'xGA',
                'xGD': 'xGDiff'
            }

            # Rename columns that exist
            for old, new in column_mapping.items():
                if old in df.columns:
                    df.rename(columns={old: new}, inplace=True)

            return df

        except Exception as e:
            print(f"Error parsing league table: {e}")
            return pd.DataFrame()

    def get_match_results(self, season: str = "2024-2025", limit: int = 50) -> pd.DataFrame:
        """
        Get recent match results

        Args:
            season: Season in format "YYYY-YYYY"
            limit: Maximum number of matches to return

        Returns:
            DataFrame with match results
        """
        url = f"{self.BUNDESLIGA_URL}/schedule/Bundesliga-Scores-and-Fixtures"
        soup = self._get_page(url)

        if not soup:
            return pd.DataFrame()

        try:
            # Find the fixtures table
            table = soup.find('table', {'id': re.compile(r'sched_.*_1')})

            if not table:
                table = soup.find('table', class_='stats_table')

            if not table:
                print("Could not find fixtures table")
                return pd.DataFrame()

            # Parse table
            df = pd.read_html(str(table))[0]

            # Clean up multi-level columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns.values]

            # Filter for completed matches (have a score)
            if 'Score' in df.columns:
                df = df[df['Score'].notna()].copy()

            # Rename columns
            column_mapping = {
                'Wk': 'Week',
                'Date': 'Date',
                'Time': 'Time',
                'Home': 'HomeTeam',
                'Away': 'AwayTeam',
                'Score': 'Score',
                'xG': 'xG_Home',
                'xG.1': 'xG_Away',
                'Attendance': 'Attendance',
                'Venue': 'Venue',
                'Referee': 'Referee'
            }

            for old, new in column_mapping.items():
                if old in df.columns:
                    df.rename(columns={old: new}, inplace=True)

            # Limit results
            if len(df) > limit:
                df = df.tail(limit)

            return df

        except Exception as e:
            print(f"Error parsing match results: {e}")
            return pd.DataFrame()

    def get_team_xg_stats(self, season: str = "2024-2025") -> pd.DataFrame:
        """
        Get xG statistics for all teams

        Args:
            season: Season in format "YYYY-YYYY"

        Returns:
            DataFrame with team xG statistics
        """
        url = f"{self.BUNDESLIGA_URL}/Bundesliga-Stats"
        soup = self._get_page(url)

        if not soup:
            return pd.DataFrame()

        try:
            # Look for table with xG data
            # FBref usually has this in the main standings table or a separate shooting table
            table = soup.find('table', {'id': re.compile(r'.*shooting.*')})

            if not table:
                # Try the main table which might have xG
                table = soup.find('table', {'id': 'results2024-202520_overall'})

            if not table:
                print("Could not find xG statistics table")
                return pd.DataFrame()

            df = pd.read_html(str(table))[0]

            # Clean up multi-level columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns.values]

            # Filter for relevant columns
            xg_columns = [col for col in df.columns if 'xG' in col or 'Squad' in col or 'Team' in col]

            if xg_columns:
                df = df[xg_columns]

            return df

        except Exception as e:
            print(f"Error parsing xG statistics: {e}")
            return pd.DataFrame()

    def get_team_stats(self, season: str = "2024-2025") -> Dict[str, pd.DataFrame]:
        """
        Get comprehensive team statistics

        Args:
            season: Season in format "YYYY-YYYY"

        Returns:
            Dictionary with different stat categories
        """
        stats = {}

        url = f"{self.BUNDESLIGA_URL}/Bundesliga-Stats"
        soup = self._get_page(url)

        if not soup:
            return stats

        try:
            # Find all tables on the page
            tables = soup.find_all('table', class_='stats_table')

            print(f"Found {len(tables)} tables on the page")

            for table in tables[:5]:  # Limit to first 5 tables
                # Get table caption/id
                table_id = table.get('id', 'unknown')
                caption = table.find('caption')
                table_name = caption.text if caption else table_id

                try:
                    df = pd.read_html(str(table))[0]

                    # Clean up multi-level columns
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns.values]

                    stats[table_name] = df
                    print(f"  - Parsed table: {table_name}")

                except Exception as e:
                    print(f"  - Error parsing table {table_name}: {e}")
                    continue

            return stats

        except Exception as e:
            print(f"Error parsing team statistics: {e}")
            return stats

    def get_head_to_head(self, team1: str, team2: str) -> pd.DataFrame:
        """
        Get head-to-head record between two teams
        Note: This requires accessing specific team pages

        Args:
            team1: First team name
            team2: Second team name

        Returns:
            DataFrame with H2H matches
        """
        # This is more complex and would require:
        # 1. Finding team URLs
        # 2. Accessing fixtures for each team
        # 3. Filtering for matches between the two teams

        # For now, return matches from current season results
        matches = self.get_match_results()

        if matches.empty:
            return pd.DataFrame()

        # Filter for matches involving both teams
        h2h = matches[
            ((matches['HomeTeam'].str.contains(team1, case=False, na=False)) &
             (matches['AwayTeam'].str.contains(team2, case=False, na=False))) |
            ((matches['HomeTeam'].str.contains(team2, case=False, na=False)) &
             (matches['AwayTeam'].str.contains(team1, case=False, na=False)))
        ]

        return h2h


def main():
    """Test the FBref scraper"""

    print("=" * 70)
    print("FBref Scraper Test - Bundesliga Data")
    print("=" * 70)

    scraper = FBrefScraper()

    # Test 1: Get league table
    print("\n1. Bundesliga League Table:")
    print("-" * 70)
    table = scraper.get_league_table()

    if not table.empty:
        print(f"Found {len(table)} teams")
        print("\nTop 6:")
        print(table.head(6).to_string(index=False))
    else:
        print("Failed to fetch league table")

    # Test 2: Get recent match results
    print("\n\n2. Recent Match Results (Last 10):")
    print("-" * 70)
    results = scraper.get_match_results(limit=10)

    if not results.empty:
        print(f"Found {len(results)} matches")
        # Show relevant columns
        display_cols = [col for col in ['Week', 'Date', 'HomeTeam', 'AwayTeam', 'Score', 'xG_Home', 'xG_Away']
                       if col in results.columns]
        if display_cols:
            print("\n" + results[display_cols].to_string(index=False))
    else:
        print("Failed to fetch match results")

    # Test 3: Get xG statistics
    print("\n\n3. Team xG Statistics:")
    print("-" * 70)
    xg_stats = scraper.get_team_xg_stats()

    if not xg_stats.empty:
        print(f"Found xG stats for {len(xg_stats)} teams")
        print("\nTop 5:")
        print(xg_stats.head(5).to_string(index=False))
    else:
        print("Failed to fetch xG statistics")

    print("\n" + "=" * 70)
    print("FBref Scraper Test Completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
