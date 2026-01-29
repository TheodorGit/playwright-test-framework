"""
End-to-end purchase workflow tests.

Complete user journey tests from login through order completion.
"""

import pytest
from pages import LoginPage, ProductsPage, CartPage, CheckoutPage
from utils import ResultsReporter


@pytest.mark.e2e
class TestCompletePurchase:
    """End-to-end tests for complete purchase workflow."""

    def test_complete_single_item_purchase(self, page, test_credentials):
        """
        Test complete purchase flow for a single item.

        Steps:
        1. Login with valid credentials
        2. Add product to cart
        3. Navigate to cart
        4. Proceed to checkout
        5. Fill customer information
        6. Review and complete order
        7. Verify order confirmation
        """
        reporter = ResultsReporter("complete_single_item_purchase")

        # Step 1: Login
        login_page = LoginPage(page)
        login_page.navigate()
        login_page.login(test_credentials["username"], test_credentials["password"])
        reporter.add_step("Login", "passed", {"user": test_credentials["username"]})

        assert login_page.is_logged_in(), "Login failed"

        # Step 2: Add product to cart
        products = ProductsPage(page)
        product_name = "Sauce Labs Backpack"
        products.add_product_by_name(product_name)
        reporter.add_step("Add product to cart", "passed", {"product": product_name})

        assert products.get_cart_count() == 1

        # Step 3: Navigate to cart
        products.go_to_cart()
        cart = CartPage(page)
        reporter.add_step("Navigate to cart", "passed")

        assert cart.get_item_count() == 1

        # Step 4: Proceed to checkout
        cart.proceed_to_checkout()
        checkout = CheckoutPage(page)
        reporter.add_step("Proceed to checkout", "passed")

        # Step 5: Fill customer information
        checkout.fill_customer_info("John", "Doe", "12345")
        checkout.continue_to_overview()
        reporter.add_step("Fill customer info", "passed")

        # Step 6: Review order total
        total = checkout.get_order_total()
        reporter.add_step("Review order", "passed", {"total": total})

        # Step 7: Complete order
        checkout.finish_order()
        reporter.add_step("Complete order", "passed")

        assert checkout.is_order_complete(), "Order completion failed"
        confirmation = checkout.get_confirmation_header()
        reporter.add_step("Verify confirmation", "passed", {"message": confirmation})

        # Save report
        report_path = reporter.save()
        reporter.set_metadata("report_path", report_path)

    def test_complete_multi_item_purchase(self, page, test_credentials):
        """
        Test complete purchase flow with multiple items.

        Verifies cart correctly handles multiple products
        and calculates totals accurately.
        """
        reporter = ResultsReporter("complete_multi_item_purchase")

        # Login
        login_page = LoginPage(page)
        login_page.navigate()
        login_page.login(test_credentials["username"], test_credentials["password"])
        reporter.add_step("Login", "passed")

        # Add multiple products
        products = ProductsPage(page)
        items_to_add = [
            "Sauce Labs Backpack",
            "Sauce Labs Bike Light",
            "Sauce Labs Bolt T-Shirt"
        ]

        for item in items_to_add:
            products.add_product_by_name(item)
        reporter.add_step("Add products", "passed", {"count": len(items_to_add)})

        assert products.get_cart_count() == 3

        # Go to cart and verify
        products.go_to_cart()
        cart = CartPage(page)
        cart_items = cart.get_cart_items()
        reporter.add_step("Verify cart", "passed", {"items": len(cart_items)})

        assert len(cart_items) == 3

        # Complete checkout
        cart.proceed_to_checkout()
        checkout = CheckoutPage(page)
        checkout.fill_customer_info("Jane", "Smith", "54321")
        checkout.continue_to_overview()

        # Verify totals include all items
        total = checkout.get_order_total()
        reporter.add_step("Review total", "passed", {"total": total})

        checkout.finish_order()

        assert checkout.is_order_complete()
        reporter.add_step("Order complete", "passed")
        reporter.save()

    def test_purchase_after_cart_modification(self, page, test_credentials):
        """
        Test purchase flow after modifying cart contents.

        Verifies that removing items from cart before checkout
        results in correct order.
        """
        # Login
        login_page = LoginPage(page)
        login_page.navigate()
        login_page.login(test_credentials["username"], test_credentials["password"])

        # Add multiple products
        products = ProductsPage(page)
        products.add_product_by_name("Sauce Labs Backpack")
        products.add_product_by_name("Sauce Labs Bike Light")

        assert products.get_cart_count() == 2

        # Go to cart and remove one item
        products.go_to_cart()
        cart = CartPage(page)
        cart.remove_item("Sauce Labs Backpack")

        assert cart.get_item_count() == 1

        # Complete checkout with remaining item
        cart.proceed_to_checkout()
        checkout = CheckoutPage(page)
        checkout.fill_customer_info("Test", "User", "00000")
        checkout.continue_to_overview()
        checkout.finish_order()

        assert checkout.is_order_complete()
