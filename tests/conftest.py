"""
Pytest configuration and fixtures.

This module provides reusable fixtures for browser automation tests,
including browser management, authentication, and test utilities.
"""

import os
import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from config import settings
from pages import LoginPage


@pytest.fixture(scope="session")
def browser():
    """
    Session-scoped browser instance.

    Launches a single browser (BROWSER env var: chromium, firefox or
    webkit) for the entire test session. Headless mode and slow-motion
    delay come from the settings module.
    """
    with sync_playwright() as p:
        p.selectors.set_test_id_attribute("data-test")
        browser_type = getattr(p, settings.browser_name)
        browser = browser_type.launch(
            headless=settings.headless,
            slow_mo=settings.slow_mo_ms,
        )
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
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(settings.username, settings.password)

    yield page


@pytest.fixture(scope="session")
def test_credentials():
    """Provide test credentials from the settings module."""
    return {
        "username": settings.username,
        "password": settings.password,
    }


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test result on the request node for fixture access."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
