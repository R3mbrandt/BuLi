"""
Mock data for development and testing
This data simulates real Bundesliga data when APIs are not accessible
"""

import pandas as pd
from datetime import datetime, timedelta
import random

# Bundesliga teams with realistic data
BUNDESLIGA_TEAMS = {
    'Bayern München': {
        'squad_value': 850_000_000,  # in EUR
        'short_name': 'Bayern',
        'injuries': 2,
        'base_elo': 1900
    },
    'Borussia Dortmund': {
        'squad_value': 520_000_000,
        'short_name': 'Dortmund',
        'injuries': 3,
        'base_elo': 1820
    },
    'RB Leipzig': {
        'squad_value': 380_000_000,
        'short_name': 'Leipzig',
        'injuries': 1,
        'base_elo': 1780
    },
    'Bayer Leverkusen': {
        'squad_value': 420_000_000,
        'short_name': 'Leverkusen',
        'injuries': 2,
        'base_elo': 1810
    },
    'Union Berlin': {
        'squad_value': 120_000_000,
        'short_name': 'Union',
        'injuries': 4,
        'base_elo': 1680
    },
    'SC Freiburg': {
        'squad_value': 150_000_000,
        'short_name': 'Freiburg',
        'injuries': 2,
        'base_elo': 1700
    },
    'Eintracht Frankfurt': {
        'squad_value': 280_000_000,
        'short_name': 'Frankfurt',
        'injuries': 3,
        'base_elo': 1720
    },
    'VfL Wolfsburg': {
        'squad_value': 220_000_000,
        'short_name': 'Wolfsburg',
        'injuries': 2,
        'base_elo': 1710
    },
    'Mainz 05': {
        'squad_value': 140_000_000,
        'short_name': 'Mainz',
        'injuries': 1,
        'base_elo': 1650
    },
    'Borussia Mönchengladbach': {
        'squad_value': 190_000_000,
        'short_name': 'Gladbach',
        'injuries': 3,
        'base_elo': 1690
    },
    '1. FC Köln': {
        'squad_value': 110_000_000,
        'short_name': 'Köln',
        'injuries': 5,
        'base_elo': 1630
    },
    'TSG Hoffenheim': {
        'squad_value': 200_000_000,
        'short_name': 'Hoffenheim',
        'injuries': 2,
        'base_elo': 1670
    },
    'VfB Stuttgart': {
        'squad_value': 180_000_000,
        'short_name': 'Stuttgart',
        'injuries': 3,
        'base_elo': 1720
    },
    'Werder Bremen': {
        'squad_value': 130_000_000,
        'short_name': 'Bremen',
        'injuries': 2,
        'base_elo': 1660
    },
    'VfL Bochum': {
        'squad_value': 80_000_000,
        'short_name': 'Bochum',
        'injuries': 4,
        'base_elo': 1610
    },
    'FC Augsburg': {
        'squad_value': 95_000_000,
        'short_name': 'Augsburg',
        'injuries': 3,
        'base_elo': 1640
    },
    'FC Heidenheim': {
        'squad_value': 70_000_000,
        'short_name': 'Heidenheim',
        'injuries': 2,
        'base_elo': 1620
    },
    'SV Darmstadt 98': {
        'squad_value': 60_000_000,
        'short_name': 'Darmstadt',
        'injuries': 4,
        'base_elo': 1600
    }
}


def generate_mock_matches(num_matchdays: int = 15) -> pd.DataFrame:
    """
    Generate realistic mock match data

    Args:
        num_matchdays: Number of matchdays to generate

    Returns:
        DataFrame with match results including xG values
    """
    teams = list(BUNDESLIGA_TEAMS.keys())
    matches = []
    match_id = 1

    base_date = datetime.now() - timedelta(days=num_matchdays * 7)

    for matchday in range(1, num_matchdays + 1):
        # Shuffle teams for each matchday
        shuffled = teams.copy()
        random.shuffle(shuffled)

        # Create 9 matches (18 teams)
        for i in range(0, len(shuffled) - 1, 2):
            home_team = shuffled[i]
            away_team = shuffled[i + 1]

            # Get team strengths
            home_strength = BUNDESLIGA_TEAMS[home_team]['base_elo']
            away_strength = BUNDESLIGA_TEAMS[away_team]['base_elo']

            # Calculate expected goals based on ELO difference
            elo_diff = home_strength - away_strength
            home_xg = 1.5 + (elo_diff / 400) + 0.3  # Home advantage
            away_xg = 1.3 + (-elo_diff / 400)

            # Add some randomness
            home_xg = max(0.5, home_xg + random.uniform(-0.4, 0.4))
            away_xg = max(0.5, away_xg + random.uniform(-0.4, 0.4))

            # Generate actual goals (Poisson-like distribution)
            home_goals = max(0, int(random.gauss(home_xg, 1.0)))
            away_goals = max(0, int(random.gauss(away_xg, 1.0)))

            match_date = base_date + timedelta(days=matchday * 7)

            matches.append({
                'MatchID': match_id,
                'Week': matchday,
                'Date': match_date,
                'HomeTeam': home_team,
                'AwayTeam': away_team,
                'HomeGoals': home_goals,
                'AwayGoals': away_goals,
                'xG_Home': round(home_xg, 2),
                'xG_Away': round(away_xg, 2),
                'IsFinished': True,
                'Stadium': f'{home_team} Arena'
            })

            match_id += 1

    return pd.DataFrame(matches)


def generate_mock_table(matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate league table from match results

    Args:
        matches_df: DataFrame with match results

    Returns:
        DataFrame with league table
    """
    teams = list(BUNDESLIGA_TEAMS.keys())
    table_data = []

    for team in teams:
        # Filter matches for this team
        home_matches = matches_df[matches_df['HomeTeam'] == team]
        away_matches = matches_df[matches_df['AwayTeam'] == team]

        # Calculate stats
        home_wins = len(home_matches[home_matches['HomeGoals'] > home_matches['AwayGoals']])
        home_draws = len(home_matches[home_matches['HomeGoals'] == home_matches['AwayGoals']])
        home_losses = len(home_matches[home_matches['HomeGoals'] < home_matches['AwayGoals']])

        away_wins = len(away_matches[away_matches['AwayGoals'] > away_matches['HomeGoals']])
        away_draws = len(away_matches[away_matches['AwayGoals'] == away_matches['HomeGoals']])
        away_losses = len(away_matches[away_matches['AwayGoals'] < away_matches['HomeGoals']])

        wins = home_wins + away_wins
        draws = home_draws + away_draws
        losses = home_losses + away_losses

        goals_for = (home_matches['HomeGoals'].sum() + away_matches['AwayGoals'].sum())
        goals_against = (home_matches['AwayGoals'].sum() + away_matches['HomeGoals'].sum())

        points = wins * 3 + draws

        table_data.append({
            'Team': team,
            'ShortName': BUNDESLIGA_TEAMS[team]['short_name'],
            'Played': wins + draws + losses,
            'Won': wins,
            'Draw': draws,
            'Lost': losses,
            'GoalsFor': int(goals_for),
            'GoalsAgainst': int(goals_against),
            'GoalDifference': int(goals_for - goals_against),
            'Points': points,
            'SquadValue': BUNDESLIGA_TEAMS[team]['squad_value'],
            'Injuries': BUNDESLIGA_TEAMS[team]['injuries']
        })

    df = pd.DataFrame(table_data)
    df = df.sort_values(['Points', 'GoalDifference', 'GoalsFor'], ascending=[False, False, False])
    df.reset_index(drop=True, inplace=True)
    df.insert(0, 'Rank', range(1, len(df) + 1))

    return df


def get_mock_team_xg_stats(matches_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate xG statistics for all teams

    Args:
        matches_df: DataFrame with match results

    Returns:
        DataFrame with xG stats
    """
    teams = list(BUNDESLIGA_TEAMS.keys())
    xg_data = []

    for team in teams:
        home_matches = matches_df[matches_df['HomeTeam'] == team]
        away_matches = matches_df[matches_df['AwayTeam'] == team]

        xg_for = home_matches['xG_Home'].sum() + away_matches['xG_Away'].sum()
        xg_against = home_matches['xG_Away'].sum() + away_matches['xG_Home'].sum()

        num_matches = len(home_matches) + len(away_matches)

        xg_data.append({
            'Team': team,
            'xG': round(xg_for, 2),
            'xGA': round(xg_against, 2),
            'xGDiff': round(xg_for - xg_against, 2),
            'xG_per_match': round(xg_for / num_matches if num_matches > 0 else 0, 2),
            'xGA_per_match': round(xg_against / num_matches if num_matches > 0 else 0, 2)
        })

    df = pd.DataFrame(xg_data)
    df = df.sort_values('xGDiff', ascending=False)

    return df


def get_team_data(team_name: str) -> dict:
    """
    Get detailed data for a specific team

    Args:
        team_name: Name of the team

    Returns:
        Dictionary with team data
    """
    # Try exact match first
    if team_name in BUNDESLIGA_TEAMS:
        return BUNDESLIGA_TEAMS[team_name]

    # Try partial match
    for team, data in BUNDESLIGA_TEAMS.items():
        if team_name.lower() in team.lower() or team_name.lower() in data['short_name'].lower():
            return data

    return None


def main():
    """Test mock data generation"""

    print("=" * 70)
    print("Mock Data Generator - Test")
    print("=" * 70)

    # Generate matches
    print("\n1. Generating mock matches...")
    matches = generate_mock_matches(15)
    print(f"✓ Generated {len(matches)} matches\n")
    print("Sample matches:")
    print(matches.head(10)[['Week', 'HomeTeam', 'AwayTeam', 'HomeGoals', 'AwayGoals', 'xG_Home', 'xG_Away']].to_string(index=False))

    # Generate table
    print("\n\n2. Generating league table...")
    table = generate_mock_table(matches)
    print(f"✓ Generated table with {len(table)} teams\n")
    cols = ['Rank', 'Team', 'Played', 'Won', 'Draw', 'Lost', 'GoalDifference', 'Points']
    print(table[cols].to_string(index=False))

    # Generate xG stats
    print("\n\n3. Generating xG statistics...")
    xg_stats = get_mock_team_xg_stats(matches)
    print(f"✓ Generated xG stats\n")
    print(xg_stats.head(10).to_string(index=False))

    # Test team data
    print("\n\n4. Testing team data lookup...")
    team_data = get_team_data("Bayern")
    if team_data:
        print(f"✓ Found team data: {team_data}")

    print("\n" + "=" * 70)
    print("Mock Data Test Completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
