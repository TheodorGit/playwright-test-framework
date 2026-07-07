"""Login Page Object for SauceDemo application."""

from playwright.sync_api import Page

from config import settings
from .base_page import BasePage


class LoginPage(BasePage):
    """Page object for the login page."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.get_by_test_id("username")
        self.password_input = page.get_by_test_id("password")
        self.login_button = page.get_by_test_id("login-button")
        self.error_message = page.get_by_test_id("error")

    def navigate(self) -> None:
        """Navigate to the login page."""
        self.page.goto(settings.base_url)

    def login(self, username: str, password: str) -> None:
        """Perform login with provided credentials."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
