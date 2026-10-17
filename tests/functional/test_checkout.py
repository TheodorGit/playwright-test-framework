"""Checkout step one: what it demands, what it keeps, and how it is cancelled."""

import re

import pytest
from playwright.sync_api import expect

from pages import CartPage, CheckoutPage, ProductsPage

pytestmark = [pytest.mark.functional, pytest.mark.regression]

BACKPACK = "Sauce Labs Backpack"
FIRST_NAME_REQUIRED = "First Name is required"
LAST_NAME_REQUIRED = "Last Name is required"
POSTAL_CODE_REQUIRED = "Postal Code is required"


def _at_checkout(page, product: str = BACKPACK) -> CheckoutPage:
    """One item in the cart and the customer on checkout step one."""
    products = ProductsPage(page)
    products.add_product_by_name(product)
    products.go_to_cart()
    CartPage(page).proceed_to_checkout()
    return CheckoutPage(page)


def test_checkout_requires_a_first_name(authenticated_page, steps):
    checkout = _at_checkout(authenticated_page)
    checkout.continue_to_overview()

    steps.step("an empty form names the first name",
               lambda: expect(checkout.error_message).to_contain_text(
                   FIRST_NAME_REQUIRED),
               expected=f"the message: {FIRST_NAME_REQUIRED}", ui=True)
    steps.step("the order does not move on",
               lambda: expect(authenticated_page).not_to_have_url(
                   re.compile("checkout-step-two")),
               expected="still on step one, with nothing submitted")


def test_checkout_requires_a_last_name(authenticated_page, steps):
    checkout = _at_checkout(authenticated_page)
    checkout.fill_customer_info("John", "", "12345")
    checkout.continue_to_overview()

    steps.step("a missing last name is named",
               lambda: expect(checkout.error_message).to_contain_text(
                   LAST_NAME_REQUIRED),
               expected=f"the message: {LAST_NAME_REQUIRED}", ui=True)
    steps.step("the order does not move on",
               lambda: expect(authenticated_page).not_to_have_url(
                   re.compile("checkout-step-two")),
               expected="still on step one, with nothing submitted")


def test_checkout_requires_a_postal_code(authenticated_page, steps):
    checkout = _at_checkout(authenticated_page)
    checkout.fill_customer_info("John", "Doe", "")
    checkout.continue_to_overview()

    steps.step("a missing postal code is named",
               lambda: expect(checkout.error_message).to_contain_text(
                   POSTAL_CODE_REQUIRED),
               expected=f"the message: {POSTAL_CODE_REQUIRED}", ui=True)
    steps.step("the order does not move on",
               lambda: expect(authenticated_page).not_to_have_url(
                   re.compile("checkout-step-two")),
               expected="still on step one, with nothing submitted")


def test_checkout_keeps_what_was_typed(authenticated_page, steps):
    """The counterpart of DEF-03: on a sound build each field keeps its own value."""
    checkout = _at_checkout(authenticated_page)
    checkout.fill_customer_info("John", "Doe", "12345")

    steps.step("the first name holds what was typed into it",
               lambda: expect(checkout.first_name_input).to_have_value("John"),
               expected="First Name holds John", ui=True)
    steps.step("the last name holds what was typed into it",
               lambda: expect(checkout.last_name_input).to_have_value("Doe"),
               expected="Last Name holds Doe, not the first name")
    steps.step("the postal code holds what was typed into it",
               lambda: expect(checkout.postal_code_input).to_have_value("12345"),
               expected="Postal Code holds 12345")
    steps.step("the filled form moves the order on",
               lambda: _continues(authenticated_page, checkout),
               expected="checkout step two, the order overview", ui=True)
    steps.tally("items added", 1)


def test_cancel_returns_to_the_cart(authenticated_page, steps):
    checkout = _at_checkout(authenticated_page)
    checkout.cancel()

    steps.step("cancelling goes back to the cart",
               lambda: expect(authenticated_page).to_have_url(re.compile("cart")),
               expected="the cart page", ui=True)
    steps.step("the cart kept the item",
               lambda: expect(CartPage(authenticated_page).cart_items).to_have_count(1),
               expected="the one line the run added is still there")
    steps.tally("items added", 1)


def _continues(page, checkout: CheckoutPage):
    checkout.continue_to_overview()
    expect(page).to_have_url(re.compile("checkout-step-two"))
