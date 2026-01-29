"""
Pytest configuration and fixtures.

This module provides reusable fixtures for browser automation tests,
including browser management, authentication, and test utilities.
"""

import os
import pytest
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from pages import LoginPage

# Load environment variables
load_dotenv()


@pytest.fixture(scope="session")
def browser():
    """
    Session-scoped browser instance.

    Launches a single Chromium browser for the entire test session.
    Controlled by HEADLESS environment variable.

    Yields:
        Browser instance
    """
    headless = os.getenv("HEADLESS", "true").lower() == "true"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser):
    """
    Function-scoped browser context.

    Creates an isolated context for each test with clean
    cookies and storage.

    Args:
        browser: Session browser instance

    Yields:
        BrowserContext instance
    """
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext):
    """
    Function-scoped page instance.

    Creates a new page/tab for each test.

    Args:
        context: Browser context

    Yields:
        Page instance
    """
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="function")
def authenticated_page(page: Page):
    """
    Pre-authenticated page fixture.

    Logs in before yielding the page, ready for tests
    that require authentication.

    Args:
        page: Page instance

    Yields:
        Authenticated Page instance
    """
    username = os.getenv("TEST_USERNAME", "standard_user")
    password = os.getenv("TEST_PASSWORD", "secret_sauce")

    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(username, password)

    yield page


@pytest.fixture(scope="session")
def test_credentials():
    """
    Provide test credentials from environment.

    Returns:
        Dict with 'username' and 'password' keys
    """
    return {
        "username": os.getenv("TEST_USERNAME", "standard_user"),
        "password": os.getenv("TEST_PASSWORD", "secret_sauce"),
    }


@pytest.fixture(scope="session")
def performance_thresholds():
    """
    Provide performance thresholds from environment.

    Returns:
        Dict with threshold values in seconds
    """
    return {
        "login_page": float(os.getenv("LOGIN_PAGE_THRESHOLD", "5.0")),
        "navigation": float(os.getenv("NAVIGATION_THRESHOLD", "10.0")),
        "checkout": float(os.getenv("CHECKOUT_THRESHOLD", "8.0")),
    }
