"""
Login functionality tests.

Tests for user authentication including valid login,
invalid credentials, and locked user scenarios.
"""

import pytest
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
            test_credentials["password"]
        )

        assert login_page.is_logged_in(), "User should be logged in"
        assert "inventory" in page.url

    def test_invalid_password(self, page, test_credentials):
        """Test login failure with incorrect password."""
        login_page = LoginPage(page)
        login_page.navigate()

        login_page.login(test_credentials["username"], "wrong_password")

        assert not login_page.is_logged_in()
        error = login_page.get_error_message()
        assert "do not match" in error.lower()

    def test_invalid_username(self, page):
        """Test login failure with non-existent username."""
        login_page = LoginPage(page)
        login_page.navigate()

        login_page.login("invalid_user", "any_password")

        assert not login_page.is_logged_in()
        error = login_page.get_error_message()
        assert "do not match" in error.lower()

    def test_locked_out_user(self, page):
        """Test login failure for locked out user."""
        login_page = LoginPage(page)
        login_page.navigate()

        login_page.login("locked_out_user", "secret_sauce")

        assert not login_page.is_logged_in()
        error = login_page.get_error_message()
        assert "locked out" in error.lower()

    def test_empty_credentials(self, page):
        """Test login validation with empty fields."""
        login_page = LoginPage(page)
        login_page.navigate()

        login_page.login("", "")

        assert not login_page.is_logged_in()
        error = login_page.get_error_message()
        assert "username is required" in error.lower()
