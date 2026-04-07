"""
Page load time performance tests.

Measures and validates page load times against configured thresholds.
"""

import pytest
from utils import measure_load_time
from pages import LoginPage, ProductsPage, CartPage


@pytest.mark.performance
class TestPageLoadTimes:
    """Performance tests for page load times."""

    def test_login_page_load_time(self, page, performance_thresholds):
        """Test that login page loads within threshold."""
        login_page = LoginPage(page)

        result = measure_load_time(
            page,
            lambda: login_page.navigate(),
            "Login page load",
        )

        assert result["success"], f"Login page failed to load: {result.get('error')}"
        assert result["duration_seconds"] < performance_thresholds["login_page"], (
            f"Login page load time {result['duration_seconds']}s exceeds "
            f"threshold {performance_thresholds['login_page']}s"
        )

    def test_products_page_load_time(
        self,
        authenticated_page,
        performance_thresholds,
    ):
        """Test that products page loads within threshold after login."""
        result = measure_load_time(
            authenticated_page,
            lambda: authenticated_page.reload(),
            "Products page load",
        )

        assert result["success"]
        assert result["duration_seconds"] < performance_thresholds["navigation"]

    def test_cart_navigation_time(
        self,
        authenticated_page,
        performance_thresholds,
    ):
        """Test navigation time from products to cart."""
        products = ProductsPage(authenticated_page)

        result = measure_load_time(
            authenticated_page,
            lambda: products.go_to_cart(),
            "Cart navigation",
        )

        assert result["success"]
        assert result["duration_seconds"] < performance_thresholds["navigation"]

    def test_checkout_flow_performance(
        self,
        authenticated_page,
        performance_thresholds,
    ):
        """Test checkout initiation performance."""
        products = ProductsPage(authenticated_page)
        products.add_product_to_cart(0)
        products.go_to_cart()

        cart = CartPage(authenticated_page)

        result = measure_load_time(
            authenticated_page,
            lambda: cart.proceed_to_checkout(),
            "Checkout initiation",
        )

        assert result["success"]
        assert result["duration_seconds"] < performance_thresholds["checkout"]
