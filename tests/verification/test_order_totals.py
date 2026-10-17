"""
The money, checked against what the run itself put in the cart.

Nothing here reads a number and calls it plausible: the order is priced
from the catalogue the run read, and every line of the overview has to
agree with that.
"""

from pages import ProductsPage
from tests import shop

ORDER = ["Sauce Labs Backpack", "Sauce Labs Bike Light", "Sauce Labs Fleece Jacket"]


def _assert_amount(shown: str, wanted, what: str) -> str:
    found = shop.amount(shown)
    assert found == wanted, (
        f"the {what} reads {shop.money(found)}, the run's own items come to "
        f"{shop.money(wanted)}")
    return shop.money(found)


def _assert_same(found: list, wanted: list, where: str) -> int:
    missing = sorted(set(wanted) - set(found))
    extra = sorted(set(found) - set(wanted))
    assert not missing and not extra, (
        f"{where} holds {sorted(found)}; the run put in {sorted(wanted)} "
        f"(missing {missing}, unexpected {extra})")
    return len(found)


def _assert_prices(lines: dict, listed: dict) -> int:
    differing = {name: (listed[name], lines[name]["price"]) for name in listed
                 if name in lines and lines[name]["price"] != listed[name]}
    assert not differing, f"(catalogue, cart) prices differ: {differing}"
    return len(listed)


def _assert_quantities(lines: dict):
    wrong = {name: line["quantity"] for name, line in lines.items()
             if line["quantity"] != "1"}
    assert not wrong, f"a line is not for one item: {wrong}"


def _order_the_run_made(products: ProductsPage, order: list, read: dict) -> int:
    """Places the order and judges what reached the overview, in one check."""
    for name in order:
        products.add_product_by_name(name)
    checkout = products.go_to_cart().proceed_to_checkout()
    checkout.fill_customer_info("Ada", "Lovelace", "12345")
    checkout.continue_to_overview()
    read.update(checkout.order_totals())
    return _assert_same([line["name"] for line in checkout.get_overview_items()],
                        order, "the overview")


def test_order_total_matches_the_run(authenticated_page, checks):
    products = ProductsPage(authenticated_page)
    prices = [shop.amount(products.price_of(name)) for name in ORDER]
    wanted = shop.totals(prices)
    shown: dict = {}

    checks.check("the overview carries exactly the items the run added",
                 lambda: _order_the_run_made(products, ORDER, shown),
                 expected=f"{len(ORDER)} lines, one per product the run added",
                 found=lambda count: f"{count} lines, as added",
                 ui=True)
    checks.check("the item total is the sum of the prices the run read",
                 lambda: _assert_amount(shown["item total"], wanted["subtotal"],
                                        "item total"),
                 expected=f"{shop.money(wanted['subtotal'])}, the sum of "
                          f"{len(prices)} catalogue prices")
    checks.check("the tax is the published rate on that item total",
                 lambda: _assert_amount(shown["tax"], wanted["tax"], "tax"),
                 expected=f"{shop.money(wanted['tax'])}, 8 per cent of the item total")
    checks.check("the total is the item total plus that tax",
                 lambda: _assert_amount(shown["total"], wanted["total"], "total"),
                 expected=f"{shop.money(wanted['total'])}, and no rounding drift",
                 ui=True)
    checks.tally("items added", len(ORDER))


def _cart_the_run_filled(products: ProductsPage, order: list, lines: dict) -> int:
    """Fills the cart and judges what it holds, in one check."""
    for name in order:
        products.add_product_by_name(name)
    cart = products.go_to_cart()
    lines.update({item["name"]: item for item in cart.get_cart_items()})
    return _assert_same(list(lines), order, "the cart")


def test_cart_agrees_with_the_catalogue(authenticated_page, checks):
    products = ProductsPage(authenticated_page)
    listed = {name: products.price_of(name) for name in ORDER}
    lines: dict = {}

    checks.check("the cart holds a line per product, and no more",
                 lambda: _cart_the_run_filled(products, ORDER, lines),
                 expected=f"{len(ORDER)} lines, one per product added",
                 found=lambda count: f"{count} lines",
                 ui=True)
    checks.check("each line keeps the price the catalogue listed",
                 lambda: _assert_prices(lines, listed),
                 expected="every cart price equal to its catalogue price",
                 found=lambda count: f"{count} prices agree")
    checks.check("each line is for a single item",
                 lambda: _assert_quantities(lines),
                 expected="quantity 1 on every line after one add each")
    checks.tally("items added", len(ORDER))
