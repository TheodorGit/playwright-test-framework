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
        self.overview_items = page.get_by_test_id("inventory-item")
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

    def finish_order(self) -> None:
        """Complete the order."""
        self.finish_button.click()

    def cancel(self) -> None:
        """Cancel the checkout process."""
        self.cancel_button.click()

    def get_overview_items(self) -> list[dict]:
        """The lines the order overview lists, as the customer sees them."""
        items = []
        for item in self.overview_items.all():
            items.append({
                "name": item.get_by_test_id("inventory-item-name").text_content(),
                "price": item.get_by_test_id("inventory-item-price").text_content(),
                "quantity": item.get_by_test_id("item-quantity").text_content(),
            })
        return items
