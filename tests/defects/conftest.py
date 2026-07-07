"""Fixtures for the defect-detection suite."""

from typing import Callable

import pytest
from playwright.sync_api import Page

from config import settings
from pages import LoginPage


@pytest.fixture
def login_as(page: Page) -> Callable[[str], Page]:
    """
    Log in as any named SauceDemo account.

    The defect suite targets the deliberately broken builds served to
    problem_user and error_user, so it cannot reuse the standard-user
    auth state.
    """

    def _login(username: str) -> Page:
        login_page = LoginPage(page)
        login_page.navigate()
        login_page.login(username, settings.password)
        page.wait_for_url("**/inventory.html")
        return page

    return _login
