"""Test data generation utilities."""

from datetime import datetime


def generate_timestamp() -> str:
    """
    Generate a unique timestamp string.

    Returns:
        Timestamp in format 'YYYY-MM-DD HHMMSS'
    """
    return datetime.now().strftime("%Y-%m-%d %H%M%S")


def generate_unique_name(prefix: str = "Test") -> str:
    """
    Generate a unique name with timestamp suffix.

    Args:
        prefix: The prefix for the generated name

    Returns:
        String in format '{prefix}_{timestamp}'
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}"
