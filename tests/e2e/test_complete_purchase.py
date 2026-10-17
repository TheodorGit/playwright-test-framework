"""Buying something: the whole journey, from signing in to the confirmation."""

from pages import LoginPage, ProductsPage

BACKPACK = "Sauce Labs Backpack"
BIKE_LIGHT = "Sauce Labs Bike Light"
BOLT_SHIRT = "Sauce Labs Bolt T-Shirt"
THANK_YOU = "Thank you for your order!"


def _sign_in(page, credentials: dict) -> ProductsPage:
    login = LoginPage(page)
    login.navigate()
    login.sign_in(credentials["username"], credentials["password"])
    return ProductsPage(page).opened()


def _assert_same(found: list, wanted: list, where: str) -> list:
    missing = sorted(set(wanted) - set(found))
    extra = sorted(set(found) - set(wanted))
    assert not missing and not extra, (
        f"{where} holds {sorted(found)}; the run put in {sorted(wanted)} "
        f"(missing {missing}, unexpected {extra})")
    return sorted(found)


def _names(lines: list) -> list:
    return sorted(line["name"] for line in lines)


def _priced(totals: dict) -> str:
    total = totals["total"]
    assert any(char.isdigit() for char in total), f"the overview shows {total!r}"
    return total


def _add_and_count(products: ProductsPage, names: list, expected: int) -> int:
    """Adding belongs to this check: a build that ignores a click fails here."""
    for name in names:
        products.add_product_by_name(name)
    return _assert_badge(products, expected)


def _assert_badge(products: ProductsPage, expected: int) -> int:
    count = products.cart_count()
    assert count == expected, f"the badge says {count}, the run added {expected}"
    return count


def test_single_item_purchase(page, checks, test_credentials):
    products = _sign_in(page, test_credentials)
    checks.check("the customer reaches the catalogue",
                 lambda: products.get_product_names(),
                 expected="signed in, with the catalogue listed",
                 found=lambda names: f"{len(names)} products listed",
                 ui=True)

    checks.check("the badge counts the one item added",
                 lambda: _add_and_count(products, [BACKPACK], 1),
                 expected="a badge reading 1")

    cart = products.go_to_cart()
    checks.check("the cart holds exactly that item",
                 lambda: _assert_same(_names(cart.get_cart_items()), [BACKPACK],
                                      "the cart"),
                 expected=f"one line: {BACKPACK}", ui=True)

    checkout = cart.proceed_to_checkout()
    checkout.fill_customer_info("John", "Doe", "12345")
    checkout.continue_to_overview()
    checks.check("the overview lists exactly what the cart held",
                 lambda: _assert_same(_names(checkout.get_overview_items()),
                                      [BACKPACK], "the overview"),
                 expected=f"one line: {BACKPACK}", ui=True)
    checks.check("the overview prices the order",
                 lambda: _priced(checkout.order_totals()),
                 expected="a total, which the verification stage then recomputes")

    checks.check("the order is confirmed",
                 lambda: checkout.finish_order(),
                 expected=f"the confirmation: {THANK_YOU}", ui=True)
    checks.tally("items added", 1)
    checks.tally("orders placed", 1)


def test_multi_item_purchase(page, checks, test_credentials):
    wanted = [BACKPACK, BIKE_LIGHT, BOLT_SHIRT]
    products = _sign_in(page, test_credentials)
    checks.check("the badge counts every item added",
                 lambda: _add_and_count(products, wanted, len(wanted)),
                 expected=f"a badge reading {len(wanted)}", ui=True)

    cart = products.go_to_cart()
    checks.check("the cart holds all three, and nothing else",
                 lambda: _assert_same(_names(cart.get_cart_items()), wanted,
                                      "the cart"),
                 expected="three lines, one per product added", ui=True)

    checkout = cart.proceed_to_checkout()
    checkout.fill_customer_info("Jane", "Smith", "54321")
    checkout.continue_to_overview()
    checks.check("the overview carries all three into the order",
                 lambda: _assert_same(_names(checkout.get_overview_items()), wanted,
                                      "the overview"),
                 expected="the same three lines", ui=True)

    checks.check("the order is confirmed",
                 lambda: checkout.finish_order(),
                 expected=f"the confirmation: {THANK_YOU}", ui=True)
    checks.tally("items added", len(wanted))
    checks.tally("orders placed", 1)


def test_purchase_after_removing_a_line(page, checks, test_credentials):
    products = _sign_in(page, test_credentials)
    for name in (BACKPACK, BIKE_LIGHT):
        products.add_product_by_name(name)
    cart = products.go_to_cart()
    cart.remove_item(BACKPACK)

    checks.check("the cart keeps only what was left in it",
                 lambda: _assert_same(_names(cart.get_cart_items()), [BIKE_LIGHT],
                                      "the cart"),
                 expected=f"one line: {BIKE_LIGHT}", ui=True)

    checkout = cart.proceed_to_checkout()
    checkout.fill_customer_info("Test", "User", "00000")
    checkout.continue_to_overview()
    checks.check("the removed item does not come back in the order",
                 lambda: _assert_same(_names(checkout.get_overview_items()),
                                      [BIKE_LIGHT], "the overview"),
                 expected=f"{BIKE_LIGHT} alone, with no trace of {BACKPACK}",
                 ui=True)

    checks.check("the order is confirmed",
                 lambda: checkout.finish_order(),
                 expected=f"the confirmation: {THANK_YOU}", ui=True)
    checks.tally("items added", 2)
    checks.tally("orders placed", 1)
