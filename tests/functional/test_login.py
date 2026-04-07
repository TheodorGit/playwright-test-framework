"""
Login functionality tests.

Tests for user authentication including valid login,
invalid credentials, and locked user scenarios.
"""

import re
import pytest
from playwright.sync_api import expect

from pages import LoginPage


@pytest.mark.functional
@pytest.mark.smoke
class TestLogin:
    """Test suite for login functionality."""

    def test_valid_login(self, page, test_credentials):
        """Test successful login with valid credentials."""
        login_page = LoginPage(page)
        login_page.navigate()

        login_page.login(
            test_credentials["username"],
            test_credentials["password"],
        )

        expect(page).to_have_url(re.compile("inventory"))

    def test_invalid_password(self, page, test_credentials):
        """Test login failure with incorrect password."""
        login_page = LoginPage(page)
        login_page.navigate()

        login_page.login(test_credentials["username"], "wrong_password")

        expect(login_page.error_message).to_be_visible()
        expect(login_page.error_message).to_contain_text("do not match")

    def test_invalid_username(self, page):
        """Test login failure with non-existent username."""
        login_page = LoginPage(page)
        login_page.navigate()

        login_page.login("invalid_user", "any_password")

        expect(login_page.error_message).to_be_visible()
        expect(login_page.error_message).to_contain_text("do not match")

    def test_locked_out_user(self, page):
        """Test login failure for locked out user."""
        login_page = LoginPage(page)
        login_page.navigate()

        login_page.login("locked_out_user", "secret_sauce")

        expect(login_page.error_message).to_be_visible()
        expect(login_page.error_message).to_contain_text("locked out")

    def test_empty_credentials(self, page):
        """Test login validation with empty fields."""
        login_page = LoginPage(page)
        login_page.navigate()

        login_page.login("", "")

        expect(login_page.error_message).to_be_visible()
        expect(login_page.error_message).to_contain_text("Username is required")
