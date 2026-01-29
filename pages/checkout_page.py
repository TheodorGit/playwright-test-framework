"""Checkout Page Object for SauceDemo application."""

from playwright.sync_api import Page


class CheckoutPage:
    """Page object for the checkout flow (step one, step two, complete)."""

    # Step One - Customer Info
    FIRST_NAME_INPUT = "[data-test='firstName']"
    LAST_NAME_INPUT = "[data-test='lastName']"
    POSTAL_CODE_INPUT = "[data-test='postalCode']"
    CANCEL_BUTTON = "[data-test='cancel']"
    CONTINUE_BUTTON = "[data-test='continue']"
    ERROR_MESSAGE = "[data-test='error']"

    # Step Two - Overview
    SUMMARY_INFO = "[data-test='payment-info-value']"
    SUBTOTAL = "[data-test='subtotal-label']"
    TAX = "[data-test='tax-label']"
    TOTAL = "[data-test='total-label']"
    FINISH_BUTTON = "[data-test='finish']"

    # Complete
    COMPLETE_HEADER = "[data-test='complete-header']"
    COMPLETE_TEXT = "[data-test='complete-text']"
    BACK_HOME_BUTTON = "[data-test='back-to-products']"

    def __init__(self, page: Page):
        self.page = page

    def fill_customer_info(
        self,
        first_name: str,
        last_name: str,
        postal_code: str
    ) -> None:
        """
        Fill in the customer information form.

        Args:
            first_name: Customer's first name
            last_name: Customer's last name
            postal_code: Customer's postal/zip code
        """
        self.page.fill(self.FIRST_NAME_INPUT, first_name)
        self.page.fill(self.LAST_NAME_INPUT, last_name)
        self.page.fill(self.POSTAL_CODE_INPUT, postal_code)

    def continue_to_overview(self) -> None:
        """Continue to the order overview page."""
        self.page.click(self.CONTINUE_BUTTON)
        self.page.wait_for_load_state("networkidle")

    def get_error_message(self) -> str:
        """Get validation error message if present."""
        error = self.page.locator(self.ERROR_MESSAGE)
        if error.is_visible():
            return error.text_content()
        return ""

    def get_order_total(self) -> str:
        """Get the total order amount from overview page."""
        return self.page.locator(self.TOTAL).text_content()

    def get_subtotal(self) -> str:
        """Get the subtotal amount."""
        return self.page.locator(self.SUBTOTAL).text_content()

    def get_tax(self) -> str:
        """Get the tax amount."""
        return self.page.locator(self.TAX).text_content()

    def finish_order(self) -> None:
        """Complete the order."""
        self.page.click(self.FINISH_BUTTON)
        self.page.wait_for_load_state("networkidle")

    def get_confirmation_header(self) -> str:
        """Get the order confirmation header text."""
        return self.page.locator(self.COMPLETE_HEADER).text_content()

    def get_confirmation_text(self) -> str:
        """Get the order confirmation body text."""
        return self.page.locator(self.COMPLETE_TEXT).text_content()

    def is_order_complete(self) -> bool:
        """Check if the order was completed successfully."""
        return self.page.locator(self.COMPLETE_HEADER).is_visible()

    def back_to_products(self) -> None:
        """Return to the products page after order completion."""
        self.page.click(self.BACK_HOME_BUTTON)
        self.page.wait_for_load_state("networkidle")

    def cancel(self) -> None:
        """Cancel the checkout process."""
        self.page.click(self.CANCEL_BUTTON)
        self.page.wait_for_load_state("networkidle")
