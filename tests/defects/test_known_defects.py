"""
Defect-detection suite: the regression tests, pointed at broken builds.

SauceDemo serves deliberately buggy variants of the store to the
problem_user and error_user accounts. Each test here asserts the
CORRECT behaviour, so it genuinely fails on the defect. They are marked
xfail(strict=True): CI stays green while the failures document the bugs,
and if a bug is ever fixed the unexpected pass fails the build so the
test can be promoted into the main regression suite.

Full reproduction steps and evidence for every bug live in BUGS.md.
"""

import pytest
from playwright.sync_api import expect

from pages import ProductsPage, CartPage, CheckoutPage

pytestmark = pytest.mark.defect

PROBLEM_USER = "problem_user"
ERROR_USER = "error_user"


class TestProblemUserDefects:
    """Defects in the build served to problem_user."""

    @pytest.mark.xfail(
        reason="BUG-01: every product shows the same broken 404 image",
        strict=True,
    )
    def test_every_product_shows_its_own_image(self, login_as):
        """Each product listing must display a distinct product image."""
        page = login_as(PROBLEM_USER)
        products = ProductsPage(page)

        sources = products.get_product_image_sources()

        assert len(set(sources)) == len(sources), (
            f"Expected {len(sources)} distinct product images, "
            f"got {len(set(sources))}: {set(sources)}"
        )

    @pytest.mark.xfail(
        reason="BUG-02: price sort is silently ignored",
        strict=True,
    )
    def test_price_sort_orders_products_low_to_high(self, login_as):
        """Sorting by price (low to high) must reorder the product grid."""
        page = login_as(PROBLEM_USER)
        products = ProductsPage(page)

        products.sort_products("lohi")
        prices = [float(p.replace("$", "")) for p in products.get_product_prices()]

        assert prices == sorted(prices), f"Prices not sorted: {prices}"

    @pytest.mark.xfail(
        reason="BUG-03: Last Name input writes into the First Name field",
        strict=True,
    )
    def test_checkout_form_keeps_first_and_last_name_distinct(self, login_as):
        """Checkout inputs must hold exactly what the customer typed."""
        page = login_as(PROBLEM_USER)
        products = ProductsPage(page)
        products.add_product_by_name("Sauce Labs Backpack")
        products.go_to_cart()

        cart = CartPage(page)
        cart.proceed_to_checkout()

        checkout = CheckoutPage(page)
        checkout.fill_customer_info("John", "Doe", "12345")

        expect(checkout.first_name_input).to_have_value("John")
        expect(checkout.last_name_input).to_have_value("Doe")

    @pytest.mark.xfail(
        reason="BUG-04: Add to cart is unresponsive for some products",
        strict=True,
    )
    def test_every_product_can_be_added_to_cart(self, login_as):
        """Adding any product must update the cart badge."""
        page = login_as(PROBLEM_USER)
        products = ProductsPage(page)

        products.add_product_by_name("Sauce Labs Bolt T-Shirt")

        expect(products.cart_badge).to_have_text("1")


class TestErrorUserDefects:
    """Defects in the build served to error_user."""

    @pytest.mark.xfail(
        reason="BUG-05: price sort raises an error and does not sort",
        strict=True,
    )
    def test_price_sort_completes_without_error(self, login_as):
        """Sorting must reorder products, not raise an error dialog."""
        page = login_as(ERROR_USER)
        products = ProductsPage(page)

        products.sort_products("lohi")
        prices = [float(p.replace("$", "")) for p in products.get_product_prices()]

        assert prices == sorted(prices), f"Prices not sorted: {prices}"

    @pytest.mark.xfail(
        reason="BUG-06: Finish button does nothing, orders cannot complete",
        strict=True,
    )
    def test_order_can_be_completed(self, login_as):
        """The checkout Finish button must complete the purchase."""
        page = login_as(ERROR_USER)
        products = ProductsPage(page)
        products.add_product_by_name("Sauce Labs Backpack")
        products.go_to_cart()

        cart = CartPage(page)
        cart.proceed_to_checkout()

        checkout = CheckoutPage(page)
        checkout.fill_customer_info("John", "Doe", "12345")
        checkout.continue_to_overview()
        checkout.finish_order()

        expect(checkout.complete_header).to_be_visible()
