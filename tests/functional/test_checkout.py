"""
Checkout flow functionality tests.

Tests for the complete checkout process including
customer information, order review, and completion.
"""

import pytest
from pages import ProductsPage, CartPage, CheckoutPage


@pytest.mark.functional
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

        error = checkout.get_error_message()
        assert "first name is required" in error.lower()

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

        error = checkout.get_error_message()
        assert "last name is required" in error.lower()

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

        error = checkout.get_error_message()
        assert "postal code is required" in error.lower()

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

        total = checkout.get_order_total()
        assert "Total:" in total

    def test_cancel_checkout(self, authenticated_page):
        """Test canceling the checkout process."""
        products = ProductsPage(authenticated_page)
        products.add_product_to_cart(0)
        products.go_to_cart()

        cart = CartPage(authenticated_page)
        cart.proceed_to_checkout()

        checkout = CheckoutPage(authenticated_page)
        checkout.cancel()

        assert "cart" in authenticated_page.url
