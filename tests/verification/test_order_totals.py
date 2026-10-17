"""
The money, checked against what the run itself put in the cart.

Nothing here reads a number and calls it plausible: the order is priced
from the catalogue the run read, and every line of the overview has to
agree with that.
"""

import pytest

from pages import CartPage, CheckoutPage, ProductsPage
from tests import shop

pytestmark = [pytest.mark.verification, pytest.mark.regression]

ORDER = ["Sauce Labs Backpack", "Sauce Labs Bike Light", "Sauce Labs Fleece Jacket"]


def _assert_amount(locator, wanted, what: str):
    found = shop.amount(locator.text_content())
    assert found == wanted, (
        f"the {what} reads {shop.money(found)}, the run's own items come to "
        f"{shop.money(wanted)}")
    return shop.money(found)


def _assert_same(found: list, wanted: list, where: str):
    missing = sorted(set(wanted) - set(found))
    extra = sorted(set(found) - set(wanted))
    assert not missing and not extra, (
        f"{where} holds {sorted(found)}; the run put in {sorted(wanted)} "
        f"(missing {missing}, unexpected {extra})")
    return len(found)


def test_order_total_matches_the_run(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    prices = [shop.amount(products.price_of(name)) for name in ORDER]
    for name in ORDER:
        products.add_product_by_name(name)
    products.go_to_cart()
    CartPage(authenticated_page).proceed_to_checkout()
    checkout = CheckoutPage(authenticated_page)
    checkout.fill_customer_info("Ada", "Lovelace", "12345")
    checkout.continue_to_overview()
    wanted = shop.totals(prices)

    steps.step("the overview carries exactly the items the run added",
               lambda: _assert_same(_overview_names(checkout), ORDER, "the overview"),
               expected=f"{len(ORDER)} lines, one per product the run added",
               found=lambda count: f"{count} lines, as added",
               ui=True)
    steps.step("the item total is the sum of the prices the run read",
               lambda: _assert_amount(checkout.subtotal, wanted["subtotal"],
                                      "item total"),
               expected=f"{shop.money(wanted['subtotal'])}, the sum of "
                        f"{len(prices)} catalogue prices")
    steps.step("the tax is the published rate on that item total",
               lambda: _assert_amount(checkout.tax, wanted["tax"], "tax"),
               expected=f"{shop.money(wanted['tax'])}, 8 per cent of the item total")
    steps.step("the total is the item total plus that tax",
               lambda: _assert_amount(checkout.total, wanted["total"], "total"),
               expected=f"{shop.money(wanted['total'])}, and no rounding drift",
               ui=True)
    steps.tally("items added", len(ORDER))


def test_cart_agrees_with_the_catalogue(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    listed = {name: products.price_of(name) for name in ORDER}
    for name in ORDER:
        products.add_product_by_name(name)
    products.go_to_cart()
    cart = CartPage(authenticated_page)
    lines = {item["name"]: item for item in cart.get_cart_items()}

    steps.step("the cart holds a line per product, and no more",
               lambda: _assert_same(list(lines), ORDER, "the cart"),
               expected=f"{len(ORDER)} lines, one per product added",
               found=lambda count: f"{count} lines",
               ui=True)
    steps.step("each line keeps the price the catalogue listed",
               lambda: _assert_prices(lines, listed),
               expected="every cart price equal to its catalogue price",
               found=lambda count: f"{count} prices agree")
    steps.step("each line is for a single item",
               lambda: _assert_quantities(lines),
               expected="quantity 1 on every line after one add each")
    steps.tally("items added", len(ORDER))


def _overview_names(checkout: CheckoutPage) -> list[str]:
    return [item["name"] for item in checkout.get_overview_items()]


def _assert_prices(lines: dict, listed: dict) -> int:
    differing = {name: (listed[name], lines[name]["price"]) for name in listed
                 if name in lines and lines[name]["price"] != listed[name]}
    assert not differing, f"(catalogue, cart) prices differ: {differing}"
    return len(listed)


def _assert_quantities(lines: dict):
    wrong = {name: line["quantity"] for name, line in lines.items()
             if line["quantity"] != "1"}
    assert not wrong, f"a line is not for one item: {wrong}"
