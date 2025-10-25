#!/usr/bin/env python3
"""
Bundesliga Match Prediction Tool
Predicts match outcomes using ELO ratings, xG data, squad values, injuries, and H2H records

Usage:
    python predict.py                          # Use mock data for demo
    python predict.py --team1 "Bayern" --team2 "Dortmund"
    python predict.py --matchday 15            # Predict all matches of matchday 15
    python predict.py --live                   # Fetch live data from OpenLigaDB
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_sources.mock_data import (
    generate_mock_matches,
    generate_mock_table,
    get_mock_team_xg_stats,
    get_team_data,
    BUNDESLIGA_TEAMS
)
from data_sources.openligadb import OpenLigaDBClient
from models.elo_rating import ELORatingSystem
from models.poisson_model import PoissonMatchPredictor
from models.prediction_engine import BundesligaPredictionEngine

import pandas as pd


class BundesligaPredictor:
    """Main predictor class"""

    def __init__(self, use_live_data: bool = False):
        """
        Initialize predictor

        Args:
            use_live_data: If True, fetch live data from OpenLigaDB
        """
        self.use_live_data = use_live_data
        self.engine = BundesligaPredictionEngine()
        self.elo_system = ELORatingSystem()
        self.data_source = "mock"  # Track actual data source used

        # Load data
        if use_live_data:
            print("📡 Attempting to fetch live data from OpenLigaDB...")
            try:
                self.client = OpenLigaDBClient()
                self.matches = self.client.get_all_matches()
                self.table = self.client.get_table()

                # Validate data was actually retrieved
                if self.matches.empty or self.table.empty:
                    raise ValueError("Received empty data from API")

                print(f"✓ Successfully fetched live data!")
                self.data_source = "live"
            except Exception as e:
                print(f"\n⚠️  Live data fetch failed: {e}")
                print("📊 Falling back to mock data for demonstration...")
                print("\nPossible reasons:")
                print("  - Network restrictions or firewall")
                print("  - API temporarily unavailable")
                print("  - Your IP might be rate-limited")
                print("\n💡 Tip: Mock data provides realistic predictions for testing!\n")

                self.matches = generate_mock_matches(15)
                self.table = generate_mock_table(self.matches)
                self.use_live_data = False  # Update flag
        else:
            print("📊 Using mock data for demonstration...")
            self.matches = generate_mock_matches(15)
            self.table = generate_mock_table(self.matches)

        # Calculate ELO ratings from matches
        self._initialize_elo_ratings()

        # Get xG stats
        if self.use_live_data:
            # For live data, calculate from matches
            self.xg_stats = self._calculate_xg_from_matches()
        else:
            self.xg_stats = get_mock_team_xg_stats(self.matches)

        print(f"✓ Loaded {len(self.matches)} matches")
        print(f"✓ Loaded {len(self.table)} teams")
        print(f"✓ Data source: {self.data_source.upper()}")

    def _initialize_elo_ratings(self):
        """Calculate ELO ratings from historical matches"""
        # Set initial ratings
        if self.use_live_data:
            # Use base ratings for live data
            for team in self.table['Team']:
                self.elo_system.ratings[team] = 1500
        else:
            # Use predefined ratings for mock data
            for team, data in BUNDESLIGA_TEAMS.items():
                self.elo_system.ratings[team] = data['base_elo']

        # Process all matches to update ELO
        finished_matches = self.matches[self.matches['IsFinished'] == True]
        self.elo_system.process_matches_from_dataframe(
            finished_matches,
            initial_ratings=self.elo_system.ratings.copy()
        )

    def _calculate_xg_from_matches(self):
        """Calculate xG stats from match data (for live data without xG)"""
        teams = self.table['Team'].unique()
        xg_data = []

        # Check if xG columns exist
        has_xg = 'xG_Home' in self.matches.columns and 'xG_Away' in self.matches.columns

        for team in teams:
            home_matches = self.matches[self.matches['HomeTeam'] == team]
            away_matches = self.matches[self.matches['AwayTeam'] == team]

            # Calculate xG for and against
            if has_xg:
                # Use actual xG data if available
                xg_for = home_matches['xG_Home'].sum() + away_matches['xG_Away'].sum()
                xg_against = home_matches['xG_Away'].sum() + away_matches['xG_Home'].sum()
            else:
                # Fallback: use actual goals as proxy for xG
                # Apply slight smoothing to make it more realistic
                home_goals_for = home_matches['HomeGoals'].sum() if 'HomeGoals' in home_matches.columns else 0
                home_goals_against = home_matches['AwayGoals'].sum() if 'AwayGoals' in home_matches.columns else 0
                away_goals_for = away_matches['AwayGoals'].sum() if 'AwayGoals' in away_matches.columns else 0
                away_goals_against = away_matches['HomeGoals'].sum() if 'HomeGoals' in away_matches.columns else 0

                xg_for = home_goals_for + away_goals_for
                xg_against = home_goals_against + away_goals_against

            num_matches = len(home_matches) + len(away_matches)

            xg_data.append({
                'Team': team,
                'xG': xg_for,
                'xGA': xg_against,
                'xG_per_match': xg_for / num_matches if num_matches > 0 else 1.5,
                'xGA_per_match': xg_against / num_matches if num_matches > 0 else 1.5
            })

        df = pd.DataFrame(xg_data)

        # Add info message about data source
        if not has_xg:
            print("ℹ️  Note: Using actual goals as proxy for xG (OpenLigaDB doesn't provide xG data)")

        return df

    def get_team_data(self, team_name: str) -> dict:
        """Get comprehensive data for a team"""
        # Find team in table
        team_row = self.table[self.table['Team'].str.contains(team_name, case=False, na=False)]

        if team_row.empty:
            raise ValueError(f"Team '{team_name}' not found")

        team_full_name = team_row.iloc[0]['Team']

        # Get ELO
        elo = self.elo_system.get_rating(team_full_name)

        # Get xG stats
        xg_row = self.xg_stats[self.xg_stats['Team'] == team_full_name]
        if not xg_row.empty:
            xg_for = xg_row.iloc[0]['xG_per_match']
            xg_against = xg_row.iloc[0]['xGA_per_match']
        else:
            xg_for = 1.5
            xg_against = 1.5

        # Get squad value and injuries
        if self.use_live_data:
            squad_value = 100_000_000  # Default
            injuries = 2  # Default
        else:
            team_data = get_team_data(team_name)
            if team_data:
                squad_value = team_data['squad_value']
                injuries = team_data['injuries']
            else:
                squad_value = 100_000_000
                injuries = 2

        return {
            'full_name': team_full_name,
            'elo': elo,
            'xg_for': xg_for,
            'xg_against': xg_against,
            'squad_value': squad_value,
            'injuries': injuries
        }

    def predict_match(self, team1: str, team2: str):
        """Predict a single match"""
        print(f"\n🔮 Predicting: {team1} vs {team2}")
        print("=" * 70)

        # Get team data
        home_data = self.get_team_data(team1)
        away_data = self.get_team_data(team2)

        # Get H2H matches
        h2h = self.matches[
            ((self.matches['HomeTeam'].str.contains(team1, case=False, na=False)) &
             (self.matches['AwayTeam'].str.contains(team2, case=False, na=False))) |
            ((self.matches['HomeTeam'].str.contains(team2, case=False, na=False)) &
             (self.matches['AwayTeam'].str.contains(team1, case=False, na=False)))
        ]

        # Make prediction
        prediction = self.engine.predict_match(
            home_data['full_name'],
            away_data['full_name'],
            home_data,
            away_data,
            h2h if not h2h.empty else None
        )

        # Print report
        report = self.engine.format_prediction_report(prediction)
        print(report)

    def predict_matchday(self, matchday: int):
        """Predict all matches of a matchday"""
        print(f"\n🔮 Predicting Matchday {matchday}")
        print("=" * 70)

        matchday_matches = self.matches[self.matches['Week'] == matchday]

        if matchday_matches.empty:
            print(f"No matches found for matchday {matchday}")
            return

        for _, match in matchday_matches.iterrows():
            self.predict_match(match['HomeTeam'], match['AwayTeam'])
            print("\n")

    def show_elo_rankings(self):
        """Show current ELO rankings"""
        print("\n📊 Current ELO Rankings")
        print("=" * 70)

        rankings = self.elo_system.get_all_ratings()
        print(rankings.to_string(index=False))

    def show_table(self):
        """Show current league table"""
        print("\n📊 Current Bundesliga Table")
        print("=" * 70)

        cols = ['Rank', 'Team', 'Played', 'Won', 'Draw', 'Lost',
                'GoalsFor', 'GoalsAgainst', 'GoalDifference', 'Points']
        display_cols = [col for col in cols if col in self.table.columns]
        print(self.table[display_cols].to_string(index=False))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Bundesliga Match Prediction Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python predict.py --team1 "Bayern" --team2 "Dortmund"
  python predict.py --matchday 15
  python predict.py --live --team1 "Bayern" --team2 "Leipzig"
  python predict.py --show-elo
  python predict.py --show-table
        """
    )

    parser.add_argument('--team1', help='Home team name (partial match works)')
    parser.add_argument('--team2', help='Away team name (partial match works)')
    parser.add_argument('--matchday', type=int, help='Predict all matches of this matchday')
    parser.add_argument('--live', action='store_true', help='Use live data from OpenLigaDB')
    parser.add_argument('--show-elo', action='store_true', help='Show ELO rankings')
    parser.add_argument('--show-table', action='store_true', help='Show league table')

    args = parser.parse_args()

    # Initialize predictor (now with automatic fallback to mock data)
    predictor = BundesligaPredictor(use_live_data=args.live)

    # Execute commands
    if args.show_elo:
        predictor.show_elo_rankings()
    elif args.show_table:
        predictor.show_table()
    elif args.matchday:
        predictor.predict_matchday(args.matchday)
    elif args.team1 and args.team2:
        predictor.predict_match(args.team1, args.team2)
    else:
        # Default: Show demo prediction
        print("\n" + "=" * 70)
        print("BUNDESLIGA MATCH PREDICTION TOOL")
        print("=" * 70)
        print("\n💡 No arguments provided. Showing demo prediction...")
        print("Use --help for usage information.")

        predictor.show_table()
        print("\n")
        predictor.show_elo_rankings()
        print("\n")
        predictor.predict_match("Bayern", "Dortmund")


if __name__ == "__main__":
    main()
