"""Checkout Page Object for SauceDemo application."""

from playwright.sync_api import Page

from .base_page import BasePage


class CheckoutPage(BasePage):
    """Page object for the checkout flow (step one, step two, complete)."""

    def __init__(self, page: Page):
        super().__init__(page)
        # Step One - Customer Info
        self.first_name_input = page.get_by_test_id("firstName")
        self.last_name_input = page.get_by_test_id("lastName")
        self.postal_code_input = page.get_by_test_id("postalCode")
        self.cancel_button = page.get_by_test_id("cancel")
        self.continue_button = page.get_by_test_id("continue")
        self.error_message = page.get_by_test_id("error")

        # Step Two - Overview
        self.subtotal = page.get_by_test_id("subtotal-label")
        self.tax = page.get_by_test_id("tax-label")
        self.total = page.get_by_test_id("total-label")
        self.finish_button = page.get_by_test_id("finish")

        # Complete
        self.complete_header = page.get_by_test_id("complete-header")
        self.complete_text = page.get_by_test_id("complete-text")
        self.back_home_button = page.get_by_test_id("back-to-products")

    def fill_customer_info(
        self,
        first_name: str,
        last_name: str,
        postal_code: str,
    ) -> None:
        """Fill in the customer information form."""
        self.first_name_input.fill(first_name)
        self.last_name_input.fill(last_name)
        self.postal_code_input.fill(postal_code)

    def continue_to_overview(self) -> None:
        """Continue to the order overview page."""
        self.continue_button.click()

    def get_error_message(self) -> str:
        """Get validation error message if present."""
        if self.error_message.is_visible():
            return self.error_message.text_content()
        return ""

    def get_order_total(self) -> str:
        """Get the total order amount from overview page."""
        return self.total.text_content()

    def get_subtotal(self) -> str:
        """Get the subtotal amount."""
        return self.subtotal.text_content()

    def get_tax(self) -> str:
        """Get the tax amount."""
        return self.tax.text_content()

    def finish_order(self) -> None:
        """Complete the order."""
        self.finish_button.click()

    def get_confirmation_header(self) -> str:
        """Get the order confirmation header text."""
        return self.complete_header.text_content()

    def get_confirmation_text(self) -> str:
        """Get the order confirmation body text."""
        return self.complete_text.text_content()

    def is_order_complete(self) -> bool:
        """Check if the order was completed successfully."""
        return self.complete_header.is_visible()

    def back_to_products(self) -> None:
        """Return to the products page after order completion."""
        self.back_home_button.click()

    def cancel(self) -> None:
        """Cancel the checkout process."""
        self.cancel_button.click()
