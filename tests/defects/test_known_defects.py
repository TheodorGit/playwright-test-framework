"""
The documented defects, pinned against the builds that still carry them.

Every check here is written as the correct behaviour and run against the
broken build, so the report records what a customer would meet. A defect
that still reproduces is reported as a known issue, with its evidence and
a link to its report in docs/defects/. A check that passes means the
defect is gone, which fails the test: the signal to promote the check
into the regression suite and close the report.

Each defect also gets a positive control, in the same run: the same check
on the standard build. That is what pins a defect to a build instead of
to the storefront at large.

The clicks here use the page methods that do not wait for a result, since
the result never arriving is the defect; the checks below judge it.
"""

import pytest

from pages import CheckoutPage, ProductsPage
from tests import shop

pytestmark = pytest.mark.defect

PROBLEM_USER = "problem_user"
ERROR_USER = "error_user"
BACKPACK = "Sauce Labs Backpack"
BOLT_SHIRT = "Sauce Labs Bolt T-Shirt"
THANK_YOU = "Thank you for your order!"
LAST_NAME_REQUIRED = "Last Name is required"
SOUND_BUILD = "The storefront itself is sound: the standard build passes this check."


def _at_checkout(page, product: str = BACKPACK) -> CheckoutPage:
    """One item in the cart and the customer on checkout step one."""
    products = ProductsPage(page)
    products.add_product_by_name(product)
    return products.go_to_cart().proceed_to_checkout()


def _distinct_images(products: ProductsPage) -> int:
    sources = products.get_product_image_sources()
    distinct = sorted(set(sources))
    assert len(distinct) == len(sources), (
        f"{len(sources)} products show only {len(distinct)} distinct image(s): "
        f"{', '.join(str(source) for source in distinct)}")
    return len(distinct)


def _sorted_by_price(products: ProductsPage) -> str:
    """The sound path: the sort has to land before the grid is judged."""
    products.sort_products("lohi")
    return _in_price_order(products)


def _sort_ignored(products: ProductsPage) -> str:
    """The broken path: nothing waits, so the grid order is what speaks."""
    products.select_sort("lohi")
    return _in_price_order(products)


def _in_price_order(products: ProductsPage) -> str:
    prices = [shop.amount(text) for text in products.get_product_prices()]
    # Printed as plain text: a report is read by people, not by Python.
    read = ", ".join(shop.money(price) for price in prices)
    want = ", ".join(shop.money(price) for price in sorted(prices))
    assert prices == sorted(prices), f"the grid reads {read}, which in order is {want}"
    return f"{shop.money(prices[0])} first, {shop.money(prices[-1])} last"


def _badge_counts(products: ProductsPage, wanted: int) -> int:
    count = products.cart_count()
    label = products.cart_button_label(BOLT_SHIRT)
    assert count == wanted, (
        f"the cart badge says {count} and the button still reads {label}")
    return count


def _assert_badge(products: ProductsPage, wanted: int) -> int:
    count = products.cart_count()
    assert count == wanted, f"the cart badge says {count}, expected {wanted}"
    return count


def _cart_cleared(products: ProductsPage, name: str):
    count = products.cart_count()
    label = products.cart_button_label(name)
    assert (count, label) == (0, "Add to cart"), (
        f"after Remove the badge says {count} and the button reads {label}")


def _field_keeps(checkout: CheckoutPage, field: str, typed: str) -> str:
    found = checkout.typed_values()[field]
    assert found == typed, (
        f"the {field} field holds {found!r} after {typed!r} was typed into it")
    return found


def _names_kept(checkout: CheckoutPage, first: str, last: str):
    typed = checkout.typed_values()
    found_first = typed["First Name"]
    found_last = typed["Last Name"]
    assert (found_first, found_last) == (first, last), (
        f"the form holds First Name {found_first!r} and Last Name {found_last!r}, "
        f"not {first!r} and {last!r}")


def _refuses_empty_last_name(checkout: CheckoutPage) -> str:
    shown = checkout.continue_refused()
    assert LAST_NAME_REQUIRED in shown, (
        f"checkout complained about something else: {shown}")
    return shown


def test_each_product_shows_its_own_image(login_as, control_page, checks):
    page = login_as(PROBLEM_USER)
    broken = ProductsPage(page).opened()

    checks.known_defect("every product shows its own image",
                        lambda: _distinct_images(broken), "DEF-01",
                        expected="one distinct image per product")
    checks.check("the same check passes on the standard build",
                 lambda: _distinct_images(ProductsPage(control_page)),
                 expected="six distinct images for the standard customer",
                 found=lambda count: f"{count} distinct images",
                 means=SOUND_BUILD)
    checks.tally("defects pinned", 1)


def test_price_sort_reorders_the_grid(login_as, control_page, checks):
    page = login_as(PROBLEM_USER)
    broken = ProductsPage(page).opened()

    checks.known_defect("sorting by price reorders the grid",
                        lambda: _sort_ignored(broken), "DEF-02",
                        expected="prices ascending after Price low to high is chosen")
    checks.check("the same sort works on the standard build",
                 lambda: _sorted_by_price(ProductsPage(control_page)),
                 expected="prices ascending for the standard customer",
                 found=lambda read: read, means=SOUND_BUILD)
    checks.tally("defects pinned", 1)


def test_checkout_keeps_first_and_last_name_apart(login_as, control_page, checks):
    page = login_as(PROBLEM_USER)
    broken = _at_checkout(page)
    broken.type_customer_info("John", "Doe", "12345")

    checks.known_defect("the form keeps the first and last name apart",
                        lambda: _names_kept(broken, "John", "Doe"), "DEF-03",
                        expected="First Name John, Last Name Doe")
    control = _at_checkout(control_page)
    control.type_customer_info("John", "Doe", "12345")
    checks.check("the same form keeps them apart on the standard build",
                 lambda: _names_kept(control, "John", "Doe"),
                 expected="John and Doe in their own fields", means=SOUND_BUILD)
    checks.tally("defects pinned", 1)


def test_every_product_can_be_added_to_the_cart(login_as, control_page, checks):
    page = login_as(PROBLEM_USER)
    broken = ProductsPage(page).opened()
    broken.click_add(BOLT_SHIRT)

    checks.known_defect(f"adding {BOLT_SHIRT} reaches the cart",
                        lambda: _badge_counts(broken, 1), "DEF-04",
                        expected="a badge reading 1 after one add")
    broken.add_product_by_name(BACKPACK)
    checks.check("another product on the same build does add",
                 lambda: _assert_badge(broken, 1),
                 expected=f"{BACKPACK} counts, so the feature is not wholly dead",
                 means="Add to cart is broken for every product on this build, not "
                       "only for the ones named in the report.",
                 ui=True)
    control = ProductsPage(control_page)
    control.add_product_by_name(BOLT_SHIRT)
    checks.check(f"{BOLT_SHIRT} adds on the standard build",
                 lambda: _assert_badge(control, 1),
                 expected="a badge reading 1 for the standard customer",
                 means=SOUND_BUILD)
    checks.tally("defects pinned", 1)


def test_remove_on_the_grid_updates_the_cart(login_as, control_page, checks):
    page = login_as(PROBLEM_USER)
    broken = ProductsPage(page).opened()
    broken.add_product_by_name(BACKPACK)
    checks.check("the product the run removes is in the cart first",
                 lambda: _assert_badge(broken, 1),
                 expected="a badge reading 1 before Remove is clicked", ui=True)
    broken.click_remove(BACKPACK)

    checks.known_defect("Remove on the grid empties the cart",
                        lambda: _cart_cleared(broken, BACKPACK), "DEF-05",
                        expected="no badge, and the button back to Add to cart")
    control = ProductsPage(control_page)
    control.add_product_by_name(BACKPACK)
    control.remove_product_by_name(BACKPACK)
    checks.check("Remove works on the standard build",
                 lambda: _cart_cleared(control, BACKPACK),
                 expected="the badge gone for the standard customer",
                 means=SOUND_BUILD)
    checks.tally("defects pinned", 1)


def test_sorting_completes_without_an_error_dialog(login_as, control_page, checks):
    page = login_as(ERROR_USER)
    broken = ProductsPage(page).opened()
    dialogs = broken.watch_dialogs()

    def sorts_cleanly():
        broken.select_sort("lohi")
        if dialogs:
            # Attached before the check fails, so it lands in its evidence folder.
            checks.attach("the dialog the store raised", dialogs[0])
            raise AssertionError(f"the store raised an error dialog: {dialogs[0]}")
        return _in_price_order(broken)

    checks.known_defect("sorting completes without an error dialog",
                        sorts_cleanly, "DEF-06",
                        expected="prices ascending, and no dialog shown")
    checks.check("the same sort is quiet on the standard build",
                 lambda: _sorted_by_price(ProductsPage(control_page)),
                 expected="prices ascending, with nothing to dismiss",
                 found=lambda read: read, means=SOUND_BUILD)
    checks.tally("defects pinned", 1)


def test_an_order_can_be_completed(login_as, control_page, checks):
    page = login_as(ERROR_USER)
    broken = _at_checkout(page)
    # The Last Name field of this build takes no input, which is DEF-08.
    broken.type_customer_info("John", "", "12345")
    broken.continue_to_overview()

    checks.known_defect("the order reaches its confirmation",
                        lambda: broken.finish_order(), "DEF-07",
                        expected=f"the confirmation page: {THANK_YOU}")
    control = _at_checkout(control_page)
    control.fill_customer_info("John", "Doe", "12345")
    control.continue_to_overview()
    checks.check("the same order completes on the standard build",
                 lambda: control.finish_order(),
                 expected="the confirmation page for the standard customer",
                 means=SOUND_BUILD)
    checks.tally("defects pinned", 1)
    checks.tally("orders placed", 1)


def test_the_last_name_field_accepts_input(login_as, control_page, checks):
    page = login_as(ERROR_USER)
    broken = _at_checkout(page)
    broken.type_customer_info("John", "Doe", "12345")

    checks.known_defect("the Last Name field keeps what is typed into it",
                        lambda: _field_keeps(broken, "Last Name", "Doe"), "DEF-08",
                        expected="Last Name holds Doe after Doe is typed")
    checks.check("the First Name field on the same build does keep its input",
                 lambda: _field_keeps(broken, "First Name", "John"),
                 expected="First Name holds John, so the form is not wholly dead",
                 means="Checkout takes no input at all on this build, which is wider "
                       "than the report says.",
                 ui=True)
    control = _at_checkout(control_page)
    control.type_customer_info("John", "Doe", "12345")
    checks.check("the field keeps its input on the standard build",
                 lambda: _field_keeps(control, "Last Name", "Doe"),
                 expected="Last Name holds Doe for the standard customer",
                 means=SOUND_BUILD)
    checks.tally("defects pinned", 1)


def test_checkout_refuses_an_empty_last_name(login_as, control_page, checks):
    page = login_as(ERROR_USER)
    broken = _at_checkout(page)
    broken.type_customer_info("John", "", "12345")

    checks.known_defect("checkout refuses an order with no last name",
                        lambda: _refuses_empty_last_name(broken), "DEF-09",
                        expected=f"the message: {LAST_NAME_REQUIRED}")
    control = _at_checkout(control_page)
    control.type_customer_info("John", "", "12345")
    checks.check("the standard build refuses the same order",
                 lambda: _refuses_empty_last_name(control),
                 expected=f"the message: {LAST_NAME_REQUIRED}", means=SOUND_BUILD)
    checks.tally("defects pinned", 1)
