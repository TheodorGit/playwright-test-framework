"""The cart: what it holds, what it shows, and what removing a line leaves."""

import re

import pytest
from playwright.sync_api import expect

from pages import CartPage, ProductsPage

pytestmark = [pytest.mark.functional, pytest.mark.regression]

BACKPACK = "Sauce Labs Backpack"
BIKE_LIGHT = "Sauce Labs Bike Light"


def _lines(cart: CartPage) -> dict:
    return {item["name"]: item for item in cart.get_cart_items()}


def _assert_holds(cart: CartPage, added: list):
    lines = _lines(cart)
    missing = sorted(set(added) - set(lines))
    extra = sorted(set(lines) - set(added))
    assert not missing and not extra, (
        f"the cart holds {sorted(lines)}; the run added {sorted(added)} "
        f"(missing {missing}, unexpected {extra})")
    return lines


def test_cart_starts_empty(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    products.go_to_cart()
    cart = CartPage(authenticated_page)

    steps.step("the cart page opens",
               lambda: expect(cart.title).to_have_text("Your Cart"),
               expected="the Your Cart heading", ui=True)
    steps.step("it holds nothing before the run adds anything",
               lambda: expect(cart.cart_items).to_have_count(0),
               expected="no lines at all")


def test_cart_holds_exactly_what_was_added(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    added = [BACKPACK, BIKE_LIGHT]
    for name in added:
        products.add_product_by_name(name)
    products.go_to_cart()
    cart = CartPage(authenticated_page)

    steps.step("the cart lists exactly the products the run added",
               lambda: _assert_holds(cart, added),
               expected=f"{len(added)} lines: {added[0]} and {added[1]}, no one more",
               found=lambda lines: f"{len(lines)} lines, as added",
               ui=True)
    steps.tally("items added", len(added))


def test_cart_line_shows_name_price_and_quantity(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    listed_price = products.price_of(BACKPACK)
    products.add_product_by_name(BACKPACK)
    products.go_to_cart()
    cart = CartPage(authenticated_page)

    line = steps.step("the cart holds the one product the run added",
                      lambda: _assert_holds(cart, [BACKPACK])[BACKPACK],
                      expected=f"one line for {BACKPACK}", ui=True)
    steps.step("the line keeps the price the catalogue listed",
               lambda: _assert_equal(line["price"], listed_price, "price"),
               expected=f"{listed_price}, the price the run read in the catalogue")
    steps.step("the line is for a single item",
               lambda: _assert_equal(line["quantity"], "1", "quantity"),
               expected="quantity 1 after one add")
    steps.tally("items added", 1)


def test_removing_a_line_leaves_the_rest(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    for name in (BACKPACK, BIKE_LIGHT):
        products.add_product_by_name(name)
    products.go_to_cart()
    cart = CartPage(authenticated_page)
    cart.remove_item(BACKPACK)

    steps.step("only the removed line is gone",
               lambda: _assert_holds(cart, [BIKE_LIGHT]),
               expected=f"one line left, {BIKE_LIGHT}", ui=True)
    steps.step("the badge agrees with the lines on screen",
               lambda: _assert_badge(products, 1),
               expected="a badge reading 1")
    steps.tally("items added", 2)


def test_continue_shopping_returns_to_the_catalogue(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    products.go_to_cart()
    cart = CartPage(authenticated_page)
    cart.continue_shopping()

    steps.step("the storefront returns to the catalogue",
               lambda: expect(authenticated_page).to_have_url(re.compile("inventory")),
               expected="the inventory page", ui=True)
    steps.step("the catalogue is in place, not an empty frame",
               lambda: expect(products.inventory_items).to_have_count(6),
               expected="six products listed again")


def _assert_equal(found: str, want: str, what: str):
    assert found == want, f"the cart line shows {what} {found}, expected {want}"


def _assert_badge(products: ProductsPage, expected: int):
    count = products.cart_count()
    assert count == expected, f"the badge says {count}, the cart holds {expected}"
