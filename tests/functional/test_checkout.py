"""
Checkout flow functionality tests.

Tests for the complete checkout process including
customer information, order review, and completion.
"""

import re
import pytest
from playwright.sync_api import expect

from pages import ProductsPage, CartPage, CheckoutPage


@pytest.mark.functional
@pytest.mark.regression
class TestCheckout:
    """Test suite for checkout functionality."""

    def test_checkout_requires_info(self, authenticated_page):
        """Test that checkout validates required fields."""
        products = ProductsPage(authenticated_page)
        products.add_product_to_cart(0)
        products.go_to_cart()

        cart = CartPage(authenticated_page)
        cart.proceed_to_checkout()

        checkout = CheckoutPage(authenticated_page)
        checkout.continue_to_overview()

        expect(checkout.error_message).to_contain_text("First Name is required")

    def test_checkout_requires_last_name(self, authenticated_page):
        """Test that checkout validates last name."""
        products = ProductsPage(authenticated_page)
        products.add_product_to_cart(0)
        products.go_to_cart()

        cart = CartPage(authenticated_page)
        cart.proceed_to_checkout()

        checkout = CheckoutPage(authenticated_page)
        checkout.fill_customer_info("John", "", "12345")
        checkout.continue_to_overview()

        expect(checkout.error_message).to_contain_text("Last Name is required")

    def test_checkout_requires_postal_code(self, authenticated_page):
        """Test that checkout validates postal code."""
        products = ProductsPage(authenticated_page)
        products.add_product_to_cart(0)
        products.go_to_cart()

        cart = CartPage(authenticated_page)
        cart.proceed_to_checkout()

        checkout = CheckoutPage(authenticated_page)
        checkout.fill_customer_info("John", "Doe", "")
        checkout.continue_to_overview()

        expect(checkout.error_message).to_contain_text("Postal Code is required")

    def test_checkout_overview_shows_total(self, authenticated_page):
        """Test that order overview displays total."""
        products = ProductsPage(authenticated_page)
        products.add_product_by_name("Sauce Labs Backpack")
        products.go_to_cart()

        cart = CartPage(authenticated_page)
        cart.proceed_to_checkout()

        checkout = CheckoutPage(authenticated_page)
        checkout.fill_customer_info("John", "Doe", "12345")
        checkout.continue_to_overview()

        expect(checkout.total).to_contain_text("Total:")

    def test_cancel_checkout(self, authenticated_page):
        """Test canceling the checkout process."""
        products = ProductsPage(authenticated_page)
        products.add_product_to_cart(0)
        products.go_to_cart()

        cart = CartPage(authenticated_page)
        cart.proceed_to_checkout()

        checkout = CheckoutPage(authenticated_page)
        checkout.cancel()

        expect(authenticated_page).to_have_url(re.compile("cart"))
