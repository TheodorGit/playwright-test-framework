"""Login Page Object for SauceDemo application."""

import os
from playwright.sync_api import Page

from .base_page import BasePage


class LoginPage(BasePage):
    """Page object for the login page."""

    URL = os.getenv("TEST_ENDPOINT", "https://www.saucedemo.com/")

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.get_by_test_id("username")
        self.password_input = page.get_by_test_id("password")
        self.login_button = page.get_by_test_id("login-button")
        self.error_message = page.get_by_test_id("error")

    def navigate(self) -> None:
        """Navigate to the login page."""
        self.page.goto(self.URL)

    def login(self, username: str, password: str) -> None:
        """Perform login with provided credentials."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def get_error_message(self) -> str:
        """Get the error message displayed on failed login."""
        if self.error_message.is_visible():
            return self.error_message.text_content()
        return ""
