"""Signing in: who gets in, who is refused, and what they are told."""

import re

import pytest
from playwright.sync_api import expect

from pages import LoginPage, ProductsPage

pytestmark = [pytest.mark.functional, pytest.mark.regression]

LOCKED_USER = "locked_out_user"
UNKNOWN_USER = "invalid_user"
NO_MATCH = "Username and password do not match any user in this service"
LOCKED_OUT = "Sorry, this user has been locked out"
USERNAME_REQUIRED = "Username is required"
PASSWORD_REQUIRED = "Password is required"
INVENTORY = re.compile("inventory")


@pytest.mark.smoke
def test_sign_in_with_valid_credentials(page, steps, test_credentials):
    login = LoginPage(page)
    login.navigate()
    login.login(test_credentials["username"], test_credentials["password"])

    steps.step("the storefront opens on the catalogue",
               lambda: expect(page).to_have_url(INVENTORY),
               expected="the inventory page, not the login form", ui=True)
    steps.step("the catalogue belongs to a signed-in customer",
               lambda: expect(ProductsPage(page).title).to_have_text("Products"),
               expected="the Products heading")


def test_wrong_password_is_refused(page, steps, test_credentials):
    login = LoginPage(page)
    login.navigate()
    login.login(test_credentials["username"], "wrong_password")

    steps.step("the attempt is refused, and says why",
               lambda: expect(login.error_message).to_contain_text(NO_MATCH),
               expected=f"the message: {NO_MATCH}", ui=True)
    steps.step("the storefront stays shut",
               lambda: expect(page).not_to_have_url(INVENTORY),
               expected="still on the login form, with no session")


def test_unknown_username_is_refused(page, steps):
    login = LoginPage(page)
    login.navigate()
    login.login(UNKNOWN_USER, "any_password")

    steps.step("the attempt is refused, and says why",
               lambda: expect(login.error_message).to_contain_text(NO_MATCH),
               expected=f"the message: {NO_MATCH}", ui=True)
    steps.step("the message does not say which half was wrong",
               lambda: expect(login.error_message).not_to_contain_text("Username is"),
               expected="one message for both, so it leaks no account names")


def test_locked_out_account_is_refused(page, steps):
    login = LoginPage(page)
    login.navigate()
    login.login(LOCKED_USER, "secret_sauce")

    steps.step("the locked account is refused, and told why",
               lambda: expect(login.error_message).to_contain_text(LOCKED_OUT),
               expected=f"the message: {LOCKED_OUT}", ui=True)
    steps.step("the storefront stays shut",
               lambda: expect(page).not_to_have_url(INVENTORY),
               expected="still on the login form, with no session")


def test_empty_credentials_are_refused(page, steps):
    login = LoginPage(page)
    login.navigate()
    login.login("", "")

    steps.step("an empty form names the field it needs first",
               lambda: expect(login.error_message).to_contain_text(USERNAME_REQUIRED),
               expected=f"the message: {USERNAME_REQUIRED}", ui=True)

    login.login("standard_user", "")
    steps.step("a username without a password names the password",
               lambda: expect(login.error_message).to_contain_text(PASSWORD_REQUIRED),
               expected=f"the message: {PASSWORD_REQUIRED}", ui=True)
