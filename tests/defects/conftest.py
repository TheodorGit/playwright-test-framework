"""Fixtures for the defect suite."""

from collections.abc import Callable

import pytest
from playwright.sync_api import Page

from config import settings
from pages import LoginPage


@pytest.fixture
def login_as(page: Page) -> Callable[[str], Page]:
    """
    Signs in as any named SauceDemo account, on the recorded page.

    The defect suite drives the deliberately broken builds served to
    problem_user and error_user, so it cannot reuse the standard-user auth
    state. The standard build is reached in the same test through the
    control_page fixture, which is what each defect is measured against.
    """

    def _login(username: str) -> Page:
        login_page = LoginPage(page)
        login_page.navigate()
        login_page.sign_in(username, settings.password)
        return page

    return _login
