"""
Fixtures for the storefront suite.

Browser lifecycle, one login reused as storage state, and the evidence a
test leaves behind: a video, a trace grouped by check, and a screen after
every check that touched the page.
"""

import os
from contextlib import contextmanager
from urllib.parse import urljoin

import httpx
import pytest
from playwright.sync_api import Browser, Page, sync_playwright

from config import settings
from framework import tokens, ui
from pages import LoginPage, ProductsPage
from tests import profile  # noqa: F401  Registers this suite's report profile.

pytest_plugins = ["framework.pytest_plugin"]

VIEWPORT = {"width": 1920, "height": 1080}
VIDEO_SIZE = {"width": 1280, "height": 720}
INVENTORY = "inventory.html"


def _environment() -> str:
    mode = "headless" if settings.headless else "headed"
    return f"{settings.browser_name}, {mode}, {settings.base_url}"


# The report names the environment this run drove; the plugin reads it.
os.environ.setdefault("QA_ENVIRONMENT", _environment())


@pytest.fixture(scope="session")
def browser():
    """
    One browser for the whole session.

    BROWSER picks the engine, and headless mode and the slow-motion delay
    come from the settings module.
    """
    with sync_playwright() as playwright:
        playwright.selectors.set_test_id_attribute("data-test")
        browser_type = getattr(playwright, settings.browser_name)
        browser = browser_type.launch(headless=settings.headless,
                                      slow_mo=settings.slow_mo_ms)
        yield browser
        browser.close()


@pytest.fixture(scope="session")
def auth_state_path(browser: Browser, tmp_path_factory) -> str:
    """
    Logs in once per session and keeps the storage state.

    Authenticated tests reuse it instead of driving the login form, which
    leaves login behaviour to the tests that are about login.
    """
    state_file = tmp_path_factory.mktemp("auth") / "storage_state.json"
    context = browser.new_context(viewport=VIEWPORT)
    page = context.new_page()
    login = LoginPage(page)
    login.navigate()
    login.sign_in(settings.username, settings.password)
    context.storage_state(path=str(state_file))
    context.close()
    return str(state_file)


@contextmanager
def _recorded_page(browser, checks, node, videos, storage_state=None):
    context = browser.new_context(viewport=VIEWPORT, storage_state=storage_state,
                                  record_video_dir=str(videos),
                                  record_video_size=VIDEO_SIZE)
    page = context.new_page()
    kept = ui.BrowserEvidence(context, page, checks)
    try:
        yield page
    finally:
        kept.stop(tokens.run_dir(), ui.failed(checks, node))


@pytest.fixture
def page(browser: Browser, checks, request, tmp_path):
    """A clean page that records a video, a trace and a screen per check."""
    with _recorded_page(browser, checks, request.node, tmp_path) as page:
        yield page


@pytest.fixture
def authenticated_page(browser: Browser, checks, request, tmp_path, auth_state_path):
    """The same page, already signed in and parked on the catalogue."""
    with _recorded_page(browser, checks, request.node, tmp_path,
                        auth_state_path) as page:
        page.goto(urljoin(settings.base_url, INVENTORY))
        ProductsPage(page).opened()
        yield page


@pytest.fixture
def control_page(browser: Browser, auth_state_path) -> Page:
    """
    A page on the standard build, for a positive control in the same run.

    A defect belongs to a build only if the same check passes elsewhere,
    so the defect tests prove that here instead of claiming it.
    """
    context = browser.new_context(viewport=VIEWPORT, storage_state=auth_state_path)
    page = context.new_page()
    page.goto(urljoin(settings.base_url, INVENTORY))
    ProductsPage(page).opened()
    yield page
    context.close()


@pytest.fixture(scope="session")
def test_credentials() -> dict:
    """The account the regression suite signs in with."""
    return {"username": settings.username, "password": settings.password}


# The API layer and the verification stage share one client, so both can
# check the same booking from two directions.
SANDBOX_ADMIN = {"username": "admin", "password": "password123"}


@pytest.fixture(scope="session")
def api_client():
    """Session-scoped HTTP client bound to the API under test."""
    with httpx.Client(base_url=settings.api_base_url, timeout=30.0,
                      headers={"Accept": "application/json"}) as client:
        yield client


@pytest.fixture(scope="session")
def auth_token(api_client) -> str:
    """
    Authenticates once per session and returns the token.

    These are the sandbox's own published credentials, not secrets.
    """
    response = api_client.post("/auth", json=SANDBOX_ADMIN)
    assert response.status_code == 200, f"auth failed: {response.text}"
    token = response.json().get("token")
    assert token, f"no token in the auth response: {response.text}"
    return token


@pytest.fixture
def booking_payload() -> dict:
    """A valid booking, as the documented contract describes one."""
    return {
        "firstname": "Ada",
        "lastname": "Lovelace",
        "totalprice": 250,
        "depositpaid": True,
        "bookingdates": {"checkin": "2026-08-01", "checkout": "2026-08-05"},
        "additionalneeds": "Late checkout",
    }
