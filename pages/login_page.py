"""The sign-in page: who gets in, and what a refusal says."""

from urllib.parse import urljoin

from playwright.sync_api import Page, expect

from config import settings

from .base_page import BasePage

CATALOGUE = "inventory.html"


class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.get_by_placeholder("Username")
        self.password_input = page.get_by_placeholder("Password")
        self.login_button = page.get_by_role("button", name="Login")
        self.error_message = page.get_by_test_id("error")

    def navigate(self) -> None:
        """Opens the storefront and ends on a login form ready for input."""
        self.page.goto(settings.base_url)
        expect(self.login_button).to_be_visible()

    def click_submit(self, username: str, password: str) -> None:
        """Types the credentials and submits without waiting: the caller judges it."""
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def sign_in(self, username: str, password: str) -> None:
        """Signs in and ends on the catalogue."""
        self.click_submit(username, password)
        self.arrived_at(CATALOGUE)

    def sign_in_refused(self, username: str, password: str) -> str:
        """Submits credentials expecting a refusal, and returns what the store said."""
        self.click_submit(username, password)
        try:
            expect(self.error_message).to_be_visible()
        except AssertionError:
            raise AssertionError(f"the store accepted the credentials and opened "
                                 f"{self.where()}") from None
        return self.error_message.inner_text().strip()

    def catalogue_refuses_direct_entry(self) -> str:
        """Opens the catalogue with no session, and returns what the store said."""
        self.page.goto(urljoin(settings.base_url, CATALOGUE))
        try:
            expect(self.error_message).to_be_visible()
        except AssertionError:
            raise AssertionError(f"the catalogue opened without a session: the "
                                 f"browser is on {self.where()}") from None
        return self.error_message.inner_text().strip()
