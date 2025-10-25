"""
ClubELO Data Integration
Fetches ELO ratings for Bundesliga teams from ClubELO
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time


class ClubELOFetcher:
    """
    Fetches ELO ratings from ClubELO
    Website: http://clubelo.com/
    """

    BASE_URL = "http://clubelo.com"

    # Known Bundesliga teams and their ClubELO names
    BUNDESLIGA_TEAMS = {
        'Bayern Munich': 'BAY',
        'Borussia Dortmund': 'DOR',
        'RB Leipzig': 'RBL',
        'Bayer Leverkusen': 'LEV',
        'Union Berlin': 'FCU',
        'SC Freiburg': 'FRE',
        'Eintracht Frankfurt': 'EIN',
        'VfL Wolfsburg': 'WOB',
        'Mainz 05': 'MAI',
        'Borussia Monchengladbach': 'MGL',
        'FC Koln': 'KOE',
        'Hoffenheim': 'HOF',
        'VfB Stuttgart': 'STU',
        'Werder Bremen': 'SVW',
        'VfL Bochum': 'BOC',
        'FC Augsburg': 'FCA',
        'Hertha Berlin': 'BSC',
        'VfL Bochum': 'BOC'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

    def get_current_elo_from_csv(self) -> pd.DataFrame:
        """
        Download and parse the full ClubELO CSV file

        Returns:
            DataFrame with all teams' ELO ratings
        """
        # ClubELO provides a full CSV download
        csv_url = "http://clubelo.com/data/clubelo.csv"

        try:
            print(f"Downloading ClubELO data from {csv_url}...")
            response = self.session.get(csv_url, timeout=30)
            response.raise_for_status()

            # Parse CSV
            from io import StringIO
            df = pd.read_csv(StringIO(response.text))

            print(f"✓ Downloaded {len(df)} records")
            return df

        except requests.exceptions.RequestException as e:
            print(f"✗ Error downloading ClubELO CSV: {e}")
            return pd.DataFrame()

    def get_bundesliga_current_elo(self) -> pd.DataFrame:
        """
        Get current ELO ratings for Bundesliga teams

        Returns:
            DataFrame with Bundesliga teams and their current ELO ratings
        """
        df = self.get_current_elo_from_csv()

        if df.empty:
            return pd.DataFrame()

        # Filter for German teams (Country = GER)
        german_teams = df[df['Country'] == 'GER'].copy()

        # Get the most recent entry for each team
        german_teams['From'] = pd.to_datetime(german_teams['From'])

        # Sort by team and date to get latest entry
        german_teams = german_teams.sort_values(['Club', 'From'])
        latest_ratings = german_teams.groupby('Club').last().reset_index()

        # Sort by ELO rating
        latest_ratings = latest_ratings.sort_values('Elo', ascending=False)

        # Select relevant columns
        result = latest_ratings[['Club', 'Country', 'Level', 'Elo', 'From']].copy()
        result = result.rename(columns={'From': 'LastUpdate'})

        return result

    def get_elo_for_team(self, team_name: str) -> Optional[Dict]:
        """
        Get current ELO rating for a specific team

        Args:
            team_name: Name of the team (can be partial)

        Returns:
            Dictionary with team info and ELO or None
        """
        df = self.get_bundesliga_current_elo()

        if df.empty:
            return None

        # Try exact match first
        team_data = df[df['Club'].str.lower() == team_name.lower()]

        # Try partial match if exact match fails
        if team_data.empty:
            team_data = df[df['Club'].str.contains(team_name, case=False, na=False)]

        if not team_data.empty:
            row = team_data.iloc[0]
            return {
                'team': row['Club'],
                'elo': float(row['Elo']),
                'level': int(row['Level']),
                'last_update': str(row['LastUpdate'])
            }

        return None

    def get_elo_history(self, team_name: str, days_back: int = 365) -> pd.DataFrame:
        """
        Get historical ELO ratings for a team

        Args:
            team_name: Name of the team
            days_back: Number of days to look back

        Returns:
            DataFrame with historical ELO ratings
        """
        df = self.get_current_elo_from_csv()

        if df.empty:
            return pd.DataFrame()

        # Filter for the team
        team_data = df[df['Club'].str.contains(team_name, case=False, na=False)].copy()

        if team_data.empty:
            return pd.DataFrame()

        # Convert dates
        team_data['From'] = pd.to_datetime(team_data['From'])
        team_data['To'] = pd.to_datetime(team_data['To'])

        # Filter by date range
        cutoff_date = datetime.now() - timedelta(days=days_back)
        team_data = team_data[team_data['From'] >= cutoff_date]

        # Sort by date
        team_data = team_data.sort_values('From')

        return team_data[['From', 'To', 'Club', 'Elo', 'Level']]

    def compare_teams(self, team1: str, team2: str) -> Dict:
        """
        Compare ELO ratings of two teams

        Args:
            team1: First team name
            team2: Second team name

        Returns:
            Dictionary with comparison data
        """
        elo1 = self.get_elo_for_team(team1)
        elo2 = self.get_elo_for_team(team2)

        if not elo1 or not elo2:
            return {}

        elo_diff = elo1['elo'] - elo2['elo']

        # Calculate expected win probability using ELO formula
        # P(A wins) = 1 / (1 + 10^((elo_B - elo_A) / 400))
        expected_prob_team1 = 1 / (1 + 10 ** (-elo_diff / 400))

        return {
            'team1': elo1['team'],
            'team1_elo': elo1['elo'],
            'team2': elo2['team'],
            'team2_elo': elo2['elo'],
            'elo_difference': elo_diff,
            'team1_win_probability': expected_prob_team1,
            'team2_win_probability': 1 - expected_prob_team1
        }


def main():
    """Test the ClubELO integration"""

    print("=" * 70)
    print("ClubELO Data Fetcher - Bundesliga ELO Ratings")
    print("=" * 70)

    fetcher = ClubELOFetcher()

    # Test 1: Get current Bundesliga ratings
    print("\n1. Current Bundesliga ELO Ratings (Top 20 German teams):")
    print("-" * 70)
    bundesliga = fetcher.get_bundesliga_current_elo()

    if not bundesliga.empty:
        # Show top 20
        print(bundesliga.head(20).to_string(index=False))
        print(f"\nTotal German teams in database: {len(bundesliga)}")
    else:
        print("No data found!")

    # Test 2: Get specific team ratings
    print("\n\n2. Specific Team ELO Ratings:")
    print("-" * 70)
    test_teams = ["Bayern", "Dortmund", "Leipzig", "Leverkusen"]

    for team in test_teams:
        info = fetcher.get_elo_for_team(team)
        if info:
            print(f"{info['team']:30s}: ELO {info['elo']:.1f} (Level {info['level']})")
        else:
            print(f"{team:30s}: Not found")

    # Test 3: Compare two teams
    print("\n\n3. Team Comparison (Bayern vs Dortmund):")
    print("-" * 70)
    comparison = fetcher.compare_teams("Bayern", "Dortmund")

    if comparison:
        print(f"{comparison['team1']:30s}: ELO {comparison['team1_elo']:.1f}")
        print(f"{comparison['team2']:30s}: ELO {comparison['team2_elo']:.1f}")
        print(f"\nELO Difference: {comparison['elo_difference']:+.1f}")
        print(f"{comparison['team1']} Win Probability: {comparison['team1_win_probability']:.1%}")
        print(f"{comparison['team2']} Win Probability: {comparison['team2_win_probability']:.1%}")

    # Test 4: Get team history
    print("\n\n4. ELO History for Bayern Munich (last 90 days):")
    print("-" * 70)
    history = fetcher.get_elo_history("Bayern", days_back=90)

    if not history.empty:
        print(f"Records found: {len(history)}")
        print("\nRecent entries:")
        print(history.tail(5).to_string(index=False))
    else:
        print("No history found")

    print("\n" + "=" * 70)
    print("ClubELO Test completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
