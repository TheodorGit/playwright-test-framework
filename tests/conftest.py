"""
Pytest configuration and fixtures.

Provides browser lifecycle management, one-time authentication with
storage-state reuse, and automatic failure artifacts (screenshot +
Playwright trace) for every UI test.
"""

import os
from urllib.parse import urljoin

import pytest
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page

from config import settings
from pages import LoginPage

ARTIFACTS_DIR = "test_results"
VIEWPORT = {"width": 1920, "height": 1080}


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


@pytest.fixture(scope="session")
def auth_state_path(browser: Browser, tmp_path_factory: pytest.TempPathFactory) -> str:
    """
    Log in once per session and persist the storage state.

    Authenticated tests reuse this state instead of repeating the UI
    login flow, which keeps them fast and leaves login behaviour itself
    to the dedicated login tests.
    """
    state_file = tmp_path_factory.mktemp("auth") / "storage_state.json"

    context = browser.new_context(viewport=VIEWPORT)
    page = context.new_page()
    login_page = LoginPage(page)
    login_page.navigate()
    login_page.login(settings.username, settings.password)
    page.wait_for_url("**/inventory.html")
    context.storage_state(path=str(state_file))
    context.close()

    return str(state_file)


def _finalize_context(context: BrowserContext, request: pytest.FixtureRequest) -> None:
    """Save the Playwright trace if the test failed, then close the context."""
    rep_call = getattr(request.node, "rep_call", None)
    if rep_call is not None and rep_call.failed:
        trace_dir = os.path.join(ARTIFACTS_DIR, "traces")
        os.makedirs(trace_dir, exist_ok=True)
        context.tracing.stop(path=os.path.join(trace_dir, f"{request.node.name}.zip"))
    else:
        context.tracing.stop()
    context.close()


def _screenshot_on_failure(page: Page, request: pytest.FixtureRequest) -> None:
    """Capture a full-page screenshot if the test failed, then close the page."""
    rep_call = getattr(request.node, "rep_call", None)
    if rep_call is not None and rep_call.failed:
        screenshot_dir = os.path.join(ARTIFACTS_DIR, "screenshots")
        os.makedirs(screenshot_dir, exist_ok=True)
        page.screenshot(
            path=os.path.join(screenshot_dir, f"{request.node.name}.png"),
            full_page=True,
        )
    page.close()


@pytest.fixture
def context(browser: Browser, request: pytest.FixtureRequest):
    """
    Function-scoped, isolated browser context with tracing enabled.

    Each test gets clean cookies and storage. On failure the trace
    (screenshots + DOM snapshots) is saved to test_results/traces/.
    """
    context = browser.new_context(viewport=VIEWPORT)
    context.tracing.start(screenshots=True, snapshots=True)
    yield context
    _finalize_context(context, request)


@pytest.fixture
def page(context: BrowserContext, request: pytest.FixtureRequest):
    """Function-scoped page that screenshots itself on test failure."""
    page = context.new_page()
    yield page
    _screenshot_on_failure(page, request)


@pytest.fixture
def authenticated_context(
    browser: Browser,
    auth_state_path: str,
    request: pytest.FixtureRequest,
):
    """Isolated context pre-loaded with the session's authentication state."""
    context = browser.new_context(viewport=VIEWPORT, storage_state=auth_state_path)
    context.tracing.start(screenshots=True, snapshots=True)
    yield context
    _finalize_context(context, request)


@pytest.fixture
def authenticated_page(
    authenticated_context: BrowserContext,
    request: pytest.FixtureRequest,
):
    """
    Page already logged in and parked on the products page.

    Reuses the session's stored auth state rather than driving the login
    form, so authenticated tests skip the login UI entirely.
    """
    page = authenticated_context.new_page()
    page.goto(urljoin(settings.base_url, "inventory.html"))
    yield page
    _screenshot_on_failure(page, request)


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
