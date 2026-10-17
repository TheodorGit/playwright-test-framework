"""Checkout step one: what it demands, what it keeps, and how it is cancelled."""

from pages import CartPage, CheckoutPage, ProductsPage

BACKPACK = "Sauce Labs Backpack"
STEP_ONE = "checkout-step-one.html"
FIRST_NAME_REQUIRED = "First Name is required"
LAST_NAME_REQUIRED = "Last Name is required"
POSTAL_CODE_REQUIRED = "Postal Code is required"


def _at_checkout(page, product: str = BACKPACK) -> CheckoutPage:
    """One item in the cart and the customer on checkout step one."""
    products = ProductsPage(page)
    products.add_product_by_name(product)
    return products.go_to_cart().proceed_to_checkout()


def _refused_with(checkout: CheckoutPage, wanted: str) -> str:
    shown = checkout.continue_refused()
    assert wanted in shown, f"checkout complained about something else: {shown}"
    return shown


def _still_on_step_one(checkout: CheckoutPage) -> str:
    where = checkout.where()
    assert where == STEP_ONE, f"the order moved on to {where}"
    return where


def _holds(typed: dict, field: str, wanted: str) -> str:
    found = typed[field]
    assert found == wanted, f"the {field} field holds {found!r}, not {wanted!r}"
    return found


def _cart_holds(page, expected: int) -> int:
    lines = CartPage(page).opened().get_cart_items()
    assert len(lines) == expected, (
        f"the cart holds {len(lines)} line(s), expected {expected}")
    return len(lines)


def test_checkout_requires_a_first_name(authenticated_page, checks):
    checkout = _at_checkout(authenticated_page)

    checks.check("an empty form names the first name",
                 lambda: _refused_with(checkout, FIRST_NAME_REQUIRED),
                 expected=f"the message: {FIRST_NAME_REQUIRED}", ui=True)
    checks.check("the order does not move on",
                 lambda: _still_on_step_one(checkout),
                 expected="still on step one, with nothing submitted")


def test_checkout_requires_a_last_name(authenticated_page, checks):
    checkout = _at_checkout(authenticated_page)
    checkout.fill_customer_info("John", "", "12345")

    checks.check("a missing last name is named",
                 lambda: _refused_with(checkout, LAST_NAME_REQUIRED),
                 expected=f"the message: {LAST_NAME_REQUIRED}", ui=True)
    checks.check("the order does not move on",
                 lambda: _still_on_step_one(checkout),
                 expected="still on step one, with nothing submitted")


def test_checkout_requires_a_postal_code(authenticated_page, checks):
    checkout = _at_checkout(authenticated_page)
    checkout.fill_customer_info("John", "Doe", "")

    checks.check("a missing postal code is named",
                 lambda: _refused_with(checkout, POSTAL_CODE_REQUIRED),
                 expected=f"the message: {POSTAL_CODE_REQUIRED}", ui=True)
    checks.check("the order does not move on",
                 lambda: _still_on_step_one(checkout),
                 expected="still on step one, with nothing submitted")


def test_checkout_keeps_what_was_typed(authenticated_page, checks):
    """
    The counterpart of DEF-03: on a sound build each field keeps its own value.

    This is the one test with no second surface to prove it on, because the
    storefront never shows the customer's name again. It reads the fields it
    typed into, which is why the typing here uses the action that does not
    wait: the check has to be the thing that judges the values.
    """
    checkout = _at_checkout(authenticated_page)
    checkout.type_customer_info("John", "Doe", "12345")
    typed = checkout.typed_values()

    checks.check("the first name holds what was typed into it",
                 lambda: _holds(typed, "First Name", "John"),
                 expected="First Name holds John", ui=True)
    checks.check("the last name holds what was typed into it",
                 lambda: _holds(typed, "Last Name", "Doe"),
                 expected="Last Name holds Doe, not the first name")
    checks.check("the postal code holds what was typed into it",
                 lambda: _holds(typed, "Postal Code", "12345"),
                 expected="Postal Code holds 12345")
    checks.check("the filled form moves the order on",
                 lambda: checkout.continue_to_overview(),
                 expected="checkout step two, the order overview", ui=True)
    checks.tally("items added", 1)


def test_cancel_returns_to_the_cart(authenticated_page, checks):
    checkout = _at_checkout(authenticated_page)

    checks.check("cancelling goes back to the cart",
                 lambda: checkout.cancel(),
                 expected="the cart page", ui=True)
    checks.check("the cart kept the item",
                 lambda: _cart_holds(authenticated_page, 1),
                 expected="the one line the run added is still there")
    checks.tally("items added", 1)
