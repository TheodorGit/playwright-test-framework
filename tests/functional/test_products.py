"""
Products page functionality tests.

Tests for product listing, sorting, and add-to-cart functionality.
"""

import pytest
from pages import ProductsPage


@pytest.mark.functional
class TestProducts:
    """Test suite for products page functionality."""

    def test_products_page_loads(self, authenticated_page):
        """Test that products page displays correctly after login."""
        products = ProductsPage(authenticated_page)

        assert products.get_page_title() == "Products"
        assert products.get_product_count() == 6

    def test_all_products_have_prices(self, authenticated_page):
        """Test that all products display prices."""
        products = ProductsPage(authenticated_page)

        prices = products.get_product_prices()

        assert len(prices) == 6
        for price in prices:
            assert price.startswith("$")

    def test_add_product_to_cart(self, authenticated_page):
        """Test adding a single product to cart."""
        products = ProductsPage(authenticated_page)

        initial_count = products.get_cart_count()
        products.add_product_to_cart(0)

        assert products.get_cart_count() == initial_count + 1

    def test_add_product_by_name(self, authenticated_page):
        """Test adding a specific product by name."""
        products = ProductsPage(authenticated_page)

        products.add_product_by_name("Sauce Labs Backpack")

        assert products.get_cart_count() >= 1

    def test_remove_product_from_products_page(self, authenticated_page):
        """Test removing a product from cart while on products page."""
        products = ProductsPage(authenticated_page)

        products.add_product_by_name("Sauce Labs Backpack")
        initial_count = products.get_cart_count()

        products.remove_product_by_name("Sauce Labs Backpack")

        assert products.get_cart_count() == initial_count - 1

    def test_sort_products_price_low_to_high(self, authenticated_page):
        """Test sorting products by price ascending."""
        products = ProductsPage(authenticated_page)

        products.sort_products("lohi")
        prices = products.get_product_prices()

        # Extract numeric values
        numeric_prices = [float(p.replace("$", "")) for p in prices]

        assert numeric_prices == sorted(numeric_prices)

    def test_sort_products_price_high_to_low(self, authenticated_page):
        """Test sorting products by price descending."""
        products = ProductsPage(authenticated_page)

        products.sort_products("hilo")
        prices = products.get_product_prices()

        numeric_prices = [float(p.replace("$", "")) for p in prices]

        assert numeric_prices == sorted(numeric_prices, reverse=True)

    def test_sort_products_name_a_to_z(self, authenticated_page):
        """Test sorting products alphabetically ascending."""
        products = ProductsPage(authenticated_page)

        products.sort_products("az")
        names = products.get_product_names()

        assert names == sorted(names)

    def test_sort_products_name_z_to_a(self, authenticated_page):
        """Test sorting products alphabetically descending."""
        products = ProductsPage(authenticated_page)

        products.sort_products("za")
        names = products.get_product_names()

        assert names == sorted(names, reverse=True)
