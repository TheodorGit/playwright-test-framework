"""
End-to-end purchase workflow tests.

Complete user journey tests from login through order completion.
"""

import re
import pytest
from playwright.sync_api import expect

from pages import LoginPage, ProductsPage, CartPage, CheckoutPage


@pytest.mark.e2e
@pytest.mark.regression
class TestCompletePurchase:
    """End-to-end tests for complete purchase workflow."""

    @pytest.mark.smoke
    def test_complete_single_item_purchase(self, page, test_credentials):
        """
        Test complete purchase flow for a single item.

        Covers the full revenue path: login, add to cart, checkout,
        customer info, order review, and confirmation.
        """
        login_page = LoginPage(page)
        login_page.navigate()
        login_page.login(test_credentials["username"], test_credentials["password"])

        expect(page).to_have_url(re.compile("inventory"))

        products = ProductsPage(page)
        products.add_product_by_name("Sauce Labs Backpack")

        expect(products.cart_badge).to_have_text("1")

        products.go_to_cart()
        cart = CartPage(page)

        expect(cart.cart_items).to_have_count(1)

        cart.proceed_to_checkout()
        checkout = CheckoutPage(page)
        checkout.fill_customer_info("John", "Doe", "12345")
        checkout.continue_to_overview()

        expect(checkout.total).to_contain_text("Total: $")

        checkout.finish_order()

        expect(checkout.complete_header).to_have_text("Thank you for your order!")

    def test_complete_multi_item_purchase(self, page, test_credentials):
        """
        Test complete purchase flow with multiple items.

        Verifies cart correctly handles multiple products
        and the order completes with all of them.
        """
        login_page = LoginPage(page)
        login_page.navigate()
        login_page.login(test_credentials["username"], test_credentials["password"])

        products = ProductsPage(page)
        items_to_add = [
            "Sauce Labs Backpack",
            "Sauce Labs Bike Light",
            "Sauce Labs Bolt T-Shirt",
        ]

        for item in items_to_add:
            products.add_product_by_name(item)

        expect(products.cart_badge).to_have_text("3")

        products.go_to_cart()
        cart = CartPage(page)

        expect(cart.cart_items).to_have_count(3)

        cart.proceed_to_checkout()
        checkout = CheckoutPage(page)
        checkout.fill_customer_info("Jane", "Smith", "54321")
        checkout.continue_to_overview()

        expect(checkout.total).to_contain_text("Total: $")

        checkout.finish_order()

        expect(checkout.complete_header).to_be_visible()

    def test_purchase_after_cart_modification(self, page, test_credentials):
        """
        Test purchase flow after modifying cart contents.

        Verifies that removing items from cart before checkout
        results in correct order.
        """
        login_page = LoginPage(page)
        login_page.navigate()
        login_page.login(test_credentials["username"], test_credentials["password"])

        products = ProductsPage(page)
        products.add_product_by_name("Sauce Labs Backpack")
        products.add_product_by_name("Sauce Labs Bike Light")

        expect(products.cart_badge).to_have_text("2")

        products.go_to_cart()
        cart = CartPage(page)
        cart.remove_item("Sauce Labs Backpack")

        expect(cart.cart_items).to_have_count(1)

        cart.proceed_to_checkout()
        checkout = CheckoutPage(page)
        checkout.fill_customer_info("Test", "User", "00000")
        checkout.continue_to_overview()
        checkout.finish_order()

        expect(checkout.complete_header).to_be_visible()
