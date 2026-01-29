"""Login Page Object for SauceDemo application."""

import os
from playwright.sync_api import Page


class LoginPage:
    """Page object for the login page."""

    URL = os.getenv("TEST_ENDPOINT", "https://www.saucedemo.com/")

    # Locators
    USERNAME_INPUT = "[data-test='username']"
    PASSWORD_INPUT = "[data-test='password']"
    LOGIN_BUTTON = "[data-test='login-button']"
    ERROR_MESSAGE = "[data-test='error']"

    def __init__(self, page: Page):
        self.page = page

    def navigate(self) -> None:
        """Navigate to the login page."""
        self.page.goto(self.URL)
        self.page.wait_for_load_state("networkidle")

    def login(self, username: str, password: str) -> None:
        """
        Perform login with provided credentials.

        Args:
            username: The username to login with
            password: The password to login with
        """
        self.page.fill(self.USERNAME_INPUT, username)
        self.page.fill(self.PASSWORD_INPUT, password)
        self.page.click(self.LOGIN_BUTTON)
        self.page.wait_for_load_state("networkidle")

    def get_error_message(self) -> str:
        """Get the error message displayed on failed login."""
        error = self.page.locator(self.ERROR_MESSAGE)
        if error.is_visible():
            return error.text_content()
        return ""

    def is_logged_in(self) -> bool:
        """Check if login was successful by verifying URL change."""
        return "inventory" in self.page.url
