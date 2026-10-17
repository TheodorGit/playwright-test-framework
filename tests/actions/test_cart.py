"""The cart: what it holds, what it shows, and what removing a line leaves."""

from pages import ProductsPage

BACKPACK = "Sauce Labs Backpack"
BIKE_LIGHT = "Sauce Labs Bike Light"
CATALOGUE_SIZE = 6


def _lines(cart) -> dict:
    return {item["name"]: item for item in cart.get_cart_items()}


def _assert_holds(cart, added: list) -> dict:
    lines = _lines(cart)
    missing = sorted(set(added) - set(lines))
    extra = sorted(set(lines) - set(added))
    assert not missing and not extra, (
        f"the cart holds {sorted(lines)}; the run added {sorted(added)} "
        f"(missing {missing}, unexpected {extra})")
    return lines


def test_cart_starts_empty(authenticated_page, checks):
    products = ProductsPage(authenticated_page)
    cart = products.go_to_cart()

    checks.check("the cart opens with nothing in it",
                 lambda: _assert_holds(cart, []),
                 expected="no lines at all before the run adds anything", ui=True)
    checks.check("the header badge agrees the cart is empty",
                 lambda: _assert_badge(products, 0),
                 expected="no badge, read from the header rather than the list")


def test_cart_holds_exactly_what_was_added(authenticated_page, checks):
    products = ProductsPage(authenticated_page)
    added = [BACKPACK, BIKE_LIGHT]
    for name in added:
        products.add_product_by_name(name)
    cart = products.go_to_cart()

    checks.check("the cart lists exactly the products the run added",
                 lambda: _assert_holds(cart, added),
                 expected=f"{len(added)} lines: {added[0]} and {added[1]}, no one more",
                 found=lambda lines: f"{len(lines)} lines, as added",
                 ui=True)
    checks.tally("items added", len(added))


def test_cart_line_shows_name_price_and_quantity(authenticated_page, checks):
    products = ProductsPage(authenticated_page)
    listed_price = products.price_of(BACKPACK)
    products.add_product_by_name(BACKPACK)
    cart = products.go_to_cart()

    line = checks.check("the cart holds the one product the run added",
                        lambda: _assert_holds(cart, [BACKPACK])[BACKPACK],
                        expected=f"one line for {BACKPACK}", ui=True)
    checks.check("the line keeps the price the catalogue listed",
                 lambda: _assert_equal(line["price"], listed_price, "price"),
                 expected=f"{listed_price}, the price the run read in the catalogue")
    checks.check("the line is for a single item",
                 lambda: _assert_equal(line["quantity"], "1", "quantity"),
                 expected="quantity 1 after one add")
    checks.tally("items added", 1)


def test_removing_a_line_leaves_the_rest(authenticated_page, checks):
    products = ProductsPage(authenticated_page)
    for name in (BACKPACK, BIKE_LIGHT):
        products.add_product_by_name(name)
    cart = products.go_to_cart()
    cart.remove_item(BACKPACK)

    checks.check("only the removed line is gone",
                 lambda: _assert_holds(cart, [BIKE_LIGHT]),
                 expected=f"one line left, {BIKE_LIGHT}", ui=True)
    checks.check("the badge agrees with the lines on screen",
                 lambda: _assert_badge(products, 1),
                 expected="a badge reading 1")
    checks.tally("items added", 2)


def test_continue_shopping_returns_to_the_catalogue(authenticated_page, checks):
    products = ProductsPage(authenticated_page)
    products.add_product_by_name(BACKPACK)
    cart = products.go_to_cart()
    cart.continue_shopping()

    checks.check("the catalogue is back, with every product on it",
                 lambda: products.opened().get_product_names(),
                 expected=f"{CATALOGUE_SIZE} products listed again",
                 found=lambda names: f"{len(names)} products listed",
                 ui=True)
    checks.check("the cart survived the trip",
                 lambda: _assert_badge(products, 1),
                 expected="the badge still counts the item added before leaving")
    checks.tally("items added", 1)


def _assert_equal(found: str, want: str, what: str):
    assert found == want, f"the cart line shows {what} {found}, expected {want}"


def _assert_badge(products: ProductsPage, expected: int):
    count = products.cart_count()
    assert count == expected, f"the cart badge says {count}, expected {expected}"
