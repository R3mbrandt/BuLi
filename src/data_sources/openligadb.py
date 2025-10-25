"""
OpenLigaDB API Integration
Free and open API for German Bundesliga data
Website: https://www.openligadb.de/
API Documentation: https://api.openligadb.de/

No API key required!
No rate limits!
Perfect for Bundesliga data!
"""

import requests
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List
import json


class OpenLigaDBClient:
    """
    Client for OpenLigaDB API
    Provides free access to Bundesliga match data
    """

    BASE_URL = "https://api.openligadb.de"

    # League identifiers
    BUNDESLIGA_1 = "bl1"  # 1. Bundesliga
    BUNDESLIGA_2 = "bl2"  # 2. Bundesliga

    def __init__(self, league: str = "bl1"):
        """
        Initialize OpenLigaDB client

        Args:
            league: League identifier (default: "bl1" for 1. Bundesliga)
        """
        self.league = league
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BuLi-Prediction-Tool/1.0',
            'Accept': 'application/json'
        })

    def get_current_season(self) -> Optional[str]:
        """
        Get current season year

        Returns:
            Season year as string (e.g., "2024")
        """
        url = f"{self.BASE_URL}/getavailableleagues"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            leagues = response.json()

            # Find ALL Bundesliga seasons and get the most recent one
            bundesliga_seasons = []
            for league in leagues:
                if league.get('leagueShortcut') == self.league:
                    season = league.get('leagueSeason')
                    if season:
                        bundesliga_seasons.append(int(season))

            # Return the highest (most recent) season
            if bundesliga_seasons:
                return str(max(bundesliga_seasons))

            # Default to current year if no seasons found
            return str(datetime.now().year)

        except Exception as e:
            print(f"Error getting current season: {e}")
            return str(datetime.now().year)

    def get_all_matches(self, season: Optional[str] = None) -> pd.DataFrame:
        """
        Get all matches for a season

        Args:
            season: Season year (e.g., "2024"), defaults to current season

        Returns:
            DataFrame with all matches
        """
        if not season:
            season = self.get_current_season()

        url = f"{self.BASE_URL}/getmatchdata/{self.league}/{season}"

        try:
            print(f"Fetching matches for {self.league} season {season}...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            matches = response.json()
            print(f"✓ Received {len(matches)} matches")

            # Parse matches into DataFrame
            match_data = []

            for match in matches:
                # Extract relevant data
                match_dict = {
                    'MatchID': match.get('matchID'),
                    'Week': match.get('group', {}).get('groupOrderID'),
                    'WeekName': match.get('group', {}).get('groupName'),
                    'Date': match.get('matchDateTime'),
                    'HomeTeam': match.get('team1', {}).get('teamName'),
                    'HomeTeamID': match.get('team1', {}).get('teamId'),
                    'AwayTeam': match.get('team2', {}).get('teamName'),
                    'AwayTeamID': match.get('team2', {}).get('teamId'),
                    'IsFinished': match.get('matchIsFinished'),
                    'Location': match.get('location', {}).get('locationCity') if match.get('location') else None,
                    'Stadium': match.get('location', {}).get('locationStadium') if match.get('location') else None
                }

                # Extract result if match is finished
                if match.get('matchIsFinished'):
                    results = match.get('matchResults', [])
                    final_result = None

                    # Get final result (resultTypeID = 2 is usually the final score)
                    for result in results:
                        if result.get('resultTypeID') == 2:  # Final result
                            final_result = result
                            break

                    # If no final result, use the last result
                    if not final_result and results:
                        final_result = results[-1]

                    if final_result:
                        match_dict['HomeGoals'] = final_result.get('pointsTeam1')
                        match_dict['AwayGoals'] = final_result.get('pointsTeam2')
                        match_dict['ResultType'] = final_result.get('resultName')

                match_data.append(match_dict)

            df = pd.DataFrame(match_data)

            # Convert date to datetime
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])

            # Sort by date
            df = df.sort_values('Date')

            return df

        except requests.exceptions.RequestException as e:
            print(f"✗ Error fetching matches: {e}")
            return pd.DataFrame()
        except json.JSONDecodeError as e:
            print(f"✗ Error parsing JSON response: {e}")
            return pd.DataFrame()

    def get_current_matchday(self, season: Optional[str] = None) -> pd.DataFrame:
        """
        Get matches for current matchday

        Args:
            season: Season year, defaults to current

        Returns:
            DataFrame with current matchday matches
        """
        if not season:
            season = self.get_current_season()

        url = f"{self.BASE_URL}/getcurrentgroup/{self.league}"

        try:
            # Get current matchday number
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            current_group = response.json()

            matchday = current_group.get('groupOrderID')

            if matchday:
                return self.get_matchday(matchday, season)

        except Exception as e:
            print(f"Error getting current matchday: {e}")

        return pd.DataFrame()

    def get_matchday(self, matchday: int, season: Optional[str] = None) -> pd.DataFrame:
        """
        Get matches for a specific matchday

        Args:
            matchday: Matchday number (1-34)
            season: Season year, defaults to current

        Returns:
            DataFrame with matchday matches
        """
        if not season:
            season = self.get_current_season()

        url = f"{self.BASE_URL}/getmatchdata/{self.league}/{season}/{matchday}"

        try:
            print(f"Fetching matchday {matchday} for {self.league} season {season}...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            matches = response.json()
            print(f"✓ Received {len(matches)} matches")

            # Parse matches (similar to get_all_matches)
            match_data = []

            for match in matches:
                match_dict = {
                    'MatchID': match.get('matchID'),
                    'Week': match.get('group', {}).get('groupOrderID'),
                    'Date': match.get('matchDateTime'),
                    'HomeTeam': match.get('team1', {}).get('teamName'),
                    'AwayTeam': match.get('team2', {}).get('teamName'),
                    'IsFinished': match.get('matchIsFinished')
                }

                if match.get('matchIsFinished'):
                    results = match.get('matchResults', [])
                    if results:
                        # Get final result
                        final_result = next((r for r in results if r.get('resultTypeID') == 2), results[-1])
                        match_dict['HomeGoals'] = final_result.get('pointsTeam1')
                        match_dict['AwayGoals'] = final_result.get('pointsTeam2')

                match_data.append(match_dict)

            df = pd.DataFrame(match_data)

            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])

            return df

        except Exception as e:
            print(f"✗ Error fetching matchday: {e}")
            return pd.DataFrame()

    def get_table(self, season: Optional[str] = None) -> pd.DataFrame:
        """
        Get current league table

        Args:
            season: Season year, defaults to current

        Returns:
            DataFrame with league table
        """
        if not season:
            season = self.get_current_season()

        url = f"{self.BASE_URL}/getbltable/{self.league}/{season}"

        try:
            print(f"Fetching table for {self.league} season {season}...")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            table_data = response.json()
            print(f"✓ Received table with {len(table_data)} teams")

            # Parse table
            teams = []
            for entry in table_data:
                team_dict = {
                    'Position': entry.get('teamInfoId'),  # This might not be position
                    'Team': entry.get('teamName'),
                    'ShortName': entry.get('shortName'),
                    'TeamIcon': entry.get('teamIconUrl'),
                    'Played': entry.get('matches'),
                    'Won': entry.get('won'),
                    'Draw': entry.get('draw'),
                    'Lost': entry.get('lost'),
                    'GoalsFor': entry.get('goals'),
                    'GoalsAgainst': entry.get('opponentGoals'),
                    'GoalDifference': entry.get('goalDiff'),
                    'Points': entry.get('points')
                }
                teams.append(team_dict)

            df = pd.DataFrame(teams)

            # Sort by points and goal difference
            if not df.empty:
                df = df.sort_values(['Points', 'GoalDifference', 'GoalsFor'],
                                   ascending=[False, False, False])
                df.reset_index(drop=True, inplace=True)
                df.insert(0, 'Rank', range(1, len(df) + 1))

            return df

        except Exception as e:
            print(f"✗ Error fetching table: {e}")
            return pd.DataFrame()

    def get_team_matches(self, team_id: int, season: Optional[str] = None) -> pd.DataFrame:
        """
        Get all matches for a specific team

        Args:
            team_id: Team ID
            season: Season year, defaults to current

        Returns:
            DataFrame with team's matches
        """
        all_matches = self.get_all_matches(season)

        if all_matches.empty:
            return pd.DataFrame()

        # Filter for team's matches
        team_matches = all_matches[
            (all_matches['HomeTeamID'] == team_id) |
            (all_matches['AwayTeamID'] == team_id)
        ].copy()

        return team_matches

    def get_head_to_head(self, team1: str, team2: str, season: Optional[str] = None) -> pd.DataFrame:
        """
        Get head-to-head matches between two teams

        Args:
            team1: First team name
            team2: Second team name
            season: Season year, defaults to current

        Returns:
            DataFrame with H2H matches
        """
        all_matches = self.get_all_matches(season)

        if all_matches.empty:
            return pd.DataFrame()

        # Filter for matches between the two teams
        h2h = all_matches[
            ((all_matches['HomeTeam'].str.contains(team1, case=False, na=False)) &
             (all_matches['AwayTeam'].str.contains(team2, case=False, na=False))) |
            ((all_matches['HomeTeam'].str.contains(team2, case=False, na=False)) &
             (all_matches['AwayTeam'].str.contains(team1, case=False, na=False)))
        ].copy()

        return h2h


def main():
    """Test the OpenLigaDB client"""

    print("=" * 70)
    print("OpenLigaDB API Test - Bundesliga Data")
    print("=" * 70)

    client = OpenLigaDBClient()

    # Test 1: Get league table
    print("\n1. Bundesliga League Table:")
    print("-" * 70)
    table = client.get_table()

    if not table.empty:
        print(f"Found {len(table)} teams\n")
        display_cols = ['Rank', 'Team', 'Played', 'Won', 'Draw', 'Lost',
                       'GoalsFor', 'GoalsAgainst', 'GoalDifference', 'Points']
        print(table[display_cols].to_string(index=False))
    else:
        print("Failed to fetch table")

    # Test 2: Get all matches
    print("\n\n2. All Matches (showing last 10):")
    print("-" * 70)
    matches = client.get_all_matches()

    if not matches.empty:
        print(f"Total matches: {len(matches)}")
        finished = matches[matches['IsFinished'] == True]
        print(f"Finished matches: {len(finished)}\n")

        # Show last 10 finished matches
        display_cols = ['Week', 'Date', 'HomeTeam', 'AwayTeam', 'HomeGoals', 'AwayGoals']
        last_matches = finished.tail(10)
        print("Last 10 finished matches:")
        print(last_matches[display_cols].to_string(index=False))
    else:
        print("Failed to fetch matches")

    # Test 3: Get current matchday
    print("\n\n3. Current Matchday:")
    print("-" * 70)
    current = client.get_current_matchday()

    if not current.empty:
        print(f"Matchday {current.iloc[0]['Week']}\n")
        display_cols = ['Date', 'HomeTeam', 'AwayTeam', 'HomeGoals', 'AwayGoals', 'IsFinished']
        print(current[display_cols].to_string(index=False))
    else:
        print("Failed to fetch current matchday")

    # Test 4: Get H2H
    print("\n\n4. Head-to-Head (Bayern vs Dortmund):")
    print("-" * 70)
    h2h = client.get_head_to_head("Bayern", "Dortmund")

    if not h2h.empty:
        print(f"Found {len(h2h)} matches\n")
        display_cols = ['Date', 'HomeTeam', 'AwayTeam', 'HomeGoals', 'AwayGoals']
        print(h2h[display_cols].to_string(index=False))
    else:
        print("No H2H matches found")

    print("\n" + "=" * 70)
    print("OpenLigaDB API Test Completed Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
