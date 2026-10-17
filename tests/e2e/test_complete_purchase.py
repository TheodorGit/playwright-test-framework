"""Buying something: the whole journey, from signing in to the confirmation."""

import pytest
from playwright.sync_api import expect

from pages import CartPage, CheckoutPage, LoginPage, ProductsPage

pytestmark = [pytest.mark.e2e, pytest.mark.regression]

BACKPACK = "Sauce Labs Backpack"
BIKE_LIGHT = "Sauce Labs Bike Light"
BOLT_SHIRT = "Sauce Labs Bolt T-Shirt"
THANK_YOU = "Thank you for your order!"


def _sign_in(page, credentials: dict) -> ProductsPage:
    login = LoginPage(page)
    login.navigate()
    login.login(credentials["username"], credentials["password"])
    page.wait_for_url("**/inventory.html")
    return ProductsPage(page)


def _names_in_cart(cart: CartPage) -> list[str]:
    return sorted(item["name"] for item in cart.get_cart_items())


def _assert_same(found: list, wanted: list, where: str):
    missing = sorted(set(wanted) - set(found))
    extra = sorted(set(found) - set(wanted))
    assert not missing and not extra, (
        f"{where} holds {sorted(found)}; the run put in {sorted(wanted)} "
        f"(missing {missing}, unexpected {extra})")
    return sorted(found)


@pytest.mark.smoke
def test_single_item_purchase(page, steps, test_credentials):
    products = _sign_in(page, test_credentials)
    steps.step("the customer reaches the catalogue",
               lambda: expect(products.title).to_have_text("Products"),
               expected="signed in, on the Products page", ui=True)

    products.add_product_by_name(BACKPACK)
    steps.step("the badge counts the one item added",
               lambda: _assert_badge(products, 1),
               expected="a badge reading 1")

    products.go_to_cart()
    cart = CartPage(page)
    steps.step("the cart holds exactly that item",
               lambda: _assert_same(_names_in_cart(cart), [BACKPACK], "the cart"),
               expected=f"one line: {BACKPACK}", ui=True)

    cart.proceed_to_checkout()
    checkout = CheckoutPage(page)
    checkout.fill_customer_info("John", "Doe", "12345")
    checkout.continue_to_overview()
    steps.step("the overview lists exactly what the cart held",
               lambda: _assert_same(_overview_names(checkout), [BACKPACK],
                                    "the overview"),
               expected=f"one line: {BACKPACK}", ui=True)
    steps.step("the overview prices the order",
               lambda: expect(checkout.total).to_contain_text("Total: $"),
               expected="a total, which the verification stage then recomputes")

    checkout.finish_order()
    steps.step("the order is confirmed",
               lambda: expect(checkout.complete_header).to_have_text(THANK_YOU),
               expected=f"the confirmation: {THANK_YOU}", ui=True)
    steps.tally("items added", 1)
    steps.tally("orders placed", 1)


def test_multi_item_purchase(page, steps, test_credentials):
    wanted = [BACKPACK, BIKE_LIGHT, BOLT_SHIRT]
    products = _sign_in(page, test_credentials)
    for name in wanted:
        products.add_product_by_name(name)

    steps.step("the badge counts every item added",
               lambda: _assert_badge(products, len(wanted)),
               expected=f"a badge reading {len(wanted)}", ui=True)

    products.go_to_cart()
    cart = CartPage(page)
    steps.step("the cart holds all three, and nothing else",
               lambda: _assert_same(_names_in_cart(cart), wanted, "the cart"),
               expected="three lines, one per product added", ui=True)

    cart.proceed_to_checkout()
    checkout = CheckoutPage(page)
    checkout.fill_customer_info("Jane", "Smith", "54321")
    checkout.continue_to_overview()
    steps.step("the overview carries all three into the order",
               lambda: _assert_same(_overview_names(checkout), wanted,
                                    "the overview"),
               expected="the same three lines", ui=True)

    checkout.finish_order()
    steps.step("the order is confirmed",
               lambda: expect(checkout.complete_header).to_have_text(THANK_YOU),
               expected=f"the confirmation: {THANK_YOU}", ui=True)
    steps.tally("items added", len(wanted))
    steps.tally("orders placed", 1)


def test_purchase_after_removing_a_line(page, steps, test_credentials):
    products = _sign_in(page, test_credentials)
    for name in (BACKPACK, BIKE_LIGHT):
        products.add_product_by_name(name)
    products.go_to_cart()
    cart = CartPage(page)
    cart.remove_item(BACKPACK)

    steps.step("the cart keeps only what was left in it",
               lambda: _assert_same(_names_in_cart(cart), [BIKE_LIGHT], "the cart"),
               expected=f"one line: {BIKE_LIGHT}", ui=True)

    cart.proceed_to_checkout()
    checkout = CheckoutPage(page)
    checkout.fill_customer_info("Test", "User", "00000")
    checkout.continue_to_overview()
    steps.step("the removed item does not come back in the order",
               lambda: _assert_same(_overview_names(checkout), [BIKE_LIGHT],
                                    "the overview"),
               expected=f"{BIKE_LIGHT} alone, with no trace of {BACKPACK}",
               ui=True)

    checkout.finish_order()
    steps.step("the order is confirmed",
               lambda: expect(checkout.complete_header).to_have_text(THANK_YOU),
               expected=f"the confirmation: {THANK_YOU}", ui=True)
    steps.tally("items added", 2)
    steps.tally("orders placed", 1)


def _overview_names(checkout: CheckoutPage) -> list[str]:
    return sorted(item["name"] for item in checkout.get_overview_items())


def _assert_badge(products: ProductsPage, expected: int):
    count = products.cart_count()
    assert count == expected, f"the badge says {count}, the run added {expected}"
