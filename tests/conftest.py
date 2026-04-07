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
    """
    headless = os.getenv("HEADLESS", "true").lower() == "true"

    with sync_playwright() as p:
        p.selectors.set_test_id_attribute("data-test")
        slow_mo = int(os.getenv("SLOW_MO", "0"))
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser):
    """
    Function-scoped browser context.

    Creates an isolated context for each test with clean
    cookies and storage. Sets test_id_attribute to 'data-test'
    for get_by_test_id() support.
    """
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
    )
    context.tracing.start(screenshots=True, snapshots=True)
    yield context
    context.tracing.stop()
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext, request):
    """
    Function-scoped page instance.

    Captures a screenshot on test failure for debugging.
    """
    page = context.new_page()
    yield page

    # Capture screenshot on failure
    if request.node.rep_call and request.node.rep_call.failed:
        screenshot_dir = "test_results/screenshots"
        os.makedirs(screenshot_dir, exist_ok=True)
        screenshot_path = os.path.join(
            screenshot_dir, f"{request.node.name}.png"
        )
        page.screenshot(path=screenshot_path)

    page.close()


@pytest.fixture(scope="function")
def authenticated_page(page: Page):
    """
    Pre-authenticated page fixture.

    Logs in before yielding the page, ready for tests
    that require authentication.
    """
    username = os.getenv("TEST_USERNAME", "standard_user")
    password = os.getenv("TEST_PASSWORD", "secret_sauce")

    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(username, password)

    yield page


@pytest.fixture(scope="session")
def test_credentials():
    """Provide test credentials from environment."""
    return {
        "username": os.getenv("TEST_USERNAME", "standard_user"),
        "password": os.getenv("TEST_PASSWORD", "secret_sauce"),
    }


@pytest.fixture(scope="session")
def performance_thresholds():
    """Provide performance thresholds from environment."""
    return {
        "login_page": float(os.getenv("LOGIN_PAGE_THRESHOLD", "5.0")),
        "navigation": float(os.getenv("NAVIGATION_THRESHOLD", "10.0")),
        "checkout": float(os.getenv("CHECKOUT_THRESHOLD", "8.0")),
    }


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test result on the request node for fixture access."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
