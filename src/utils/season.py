"""
Season utility functions for dynamic season detection
"""

from datetime import datetime
from typing import Tuple


def get_current_season() -> int:
    """
    Get the current Bundesliga season year

    Bundesliga season runs from August to May of the following year.
    - If current month is January-July: Season is previous year
    - If current month is August-December: Season is current year

    Examples:
        - January 2025 → Season 2024 (2024/25 season)
        - August 2025 → Season 2025 (2025/26 season starts)
        - October 2024 → Season 2024 (2024/25 season)

    Returns:
        Season year as integer
    """
    now = datetime.now()
    year = now.year
    month = now.month

    # If we're in January-July, the season started last year
    if month < 8:
        return year - 1

    # If we're in August-December, the season is the current year
    return year


def get_season_string(season_year: int) -> str:
    """
    Convert season year to string format (e.g., 2024 → "2024-2025")

    Args:
        season_year: The starting year of the season

    Returns:
        Season string in format "YYYY-YYYY+1"
    """
    return f"{season_year}-{season_year + 1}"


def parse_season_string(season_str: str) -> int:
    """
    Parse season string to get the starting year

    Args:
        season_str: Season string like "2024-2025"

    Returns:
        Starting year of the season
    """
    return int(season_str.split('-')[0])
