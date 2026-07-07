"""
Shopping cart functionality tests.

Tests for cart operations including viewing items,
removing items, and cart persistence.
"""

import re
import pytest
from playwright.sync_api import expect

from pages import ProductsPage, CartPage


@pytest.mark.functional
@pytest.mark.regression
class TestCart:
    """Test suite for shopping cart functionality."""

    def test_view_empty_cart(self, authenticated_page):
        """Test viewing an empty cart."""
        products = ProductsPage(authenticated_page)
        products.go_to_cart()

        cart = CartPage(authenticated_page)

        expect(cart.title).to_have_text("Your Cart")
        expect(cart.cart_items).to_have_count(0)

    def test_cart_shows_added_items(self, authenticated_page):
        """Test that cart displays items added from products page."""
        products = ProductsPage(authenticated_page)
        products.add_product_by_name("Sauce Labs Backpack")
        products.add_product_by_name("Sauce Labs Bike Light")
        products.go_to_cart()

        cart = CartPage(authenticated_page)

        expect(cart.cart_items).to_have_count(2)
        items = cart.get_cart_items()
        item_names = [item["name"] for item in items]
        assert "Sauce Labs Backpack" in item_names
        assert "Sauce Labs Bike Light" in item_names

    def test_cart_item_has_correct_details(self, authenticated_page):
        """Test that cart items display correct information."""
        products = ProductsPage(authenticated_page)
        products.add_product_by_name("Sauce Labs Backpack")
        products.go_to_cart()

        cart = CartPage(authenticated_page)

        expect(cart.cart_items).to_have_count(1)
        items = cart.get_cart_items()
        item = items[0]
        assert item["name"] == "Sauce Labs Backpack"
        assert item["price"] == "$29.99"
        assert item["quantity"] == "1"

    def test_remove_item_from_cart(self, authenticated_page):
        """Test removing an item from the cart."""
        products = ProductsPage(authenticated_page)
        products.add_product_by_name("Sauce Labs Backpack")
        products.add_product_by_name("Sauce Labs Bike Light")
        products.go_to_cart()

        cart = CartPage(authenticated_page)
        cart.remove_item("Sauce Labs Backpack")

        expect(cart.cart_items).to_have_count(1)
        items = cart.get_cart_items()
        assert items[0]["name"] == "Sauce Labs Bike Light"

    def test_continue_shopping(self, authenticated_page):
        """Test returning to products page from cart."""
        products = ProductsPage(authenticated_page)
        products.go_to_cart()

        cart = CartPage(authenticated_page)
        cart.continue_shopping()

        expect(authenticated_page).to_have_url(re.compile("inventory"))
