"""Performance measurement utilities."""

import time
from typing import Callable, Any
from playwright.sync_api import Page


def wait_for_page_ready(page: Page, timeout: int = 30000) -> None:
    """
    Wait for page to be fully loaded and stable.

    Args:
        page: Playwright page instance
        timeout: Maximum wait time in milliseconds
    """
    page.wait_for_load_state("networkidle", timeout=timeout)
    page.wait_for_load_state("domcontentloaded", timeout=timeout)


def measure_load_time(
    page: Page,
    action: Callable[[], Any],
    description: str = "action"
) -> dict:
    """
    Measure the time taken for an action and subsequent page load.

    Args:
        page: Playwright page instance
        action: Function to execute and measure
        description: Description of the action being measured

    Returns:
        Dict with 'description', 'duration_seconds', 'success' keys
    """
    start_time = time.time()

    try:
        action()
        wait_for_page_ready(page)
        end_time = time.time()

        return {
            "description": description,
            "duration_seconds": round(end_time - start_time, 3),
            "success": True
        }
    except Exception as e:
        end_time = time.time()
        return {
            "description": description,
            "duration_seconds": round(end_time - start_time, 3),
            "success": False,
            "error": str(e)
        }


def measure_navigation(page: Page, url: str, description: str = "navigation") -> dict:
    """
    Measure page navigation time.

    Args:
        page: Playwright page instance
        url: URL to navigate to
        description: Description for the measurement

    Returns:
        Dict with timing information
    """
    return measure_load_time(
        page,
        lambda: page.goto(url),
        description
    )
