"""Checkout: the customer's details, the order overview, and the confirmation."""

from playwright.sync_api import Page, expect

from .base_page import BasePage

CART = "cart.html"
STEP_TWO = "checkout-step-two.html"
THANK_YOU = "Thank you for your order!"


class CheckoutPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # Step One - Customer Info
        self.first_name_input = page.get_by_placeholder("First Name")
        self.last_name_input = page.get_by_placeholder("Last Name")
        self.postal_code_input = page.get_by_placeholder("Zip/Postal Code")
        self.cancel_button = page.get_by_role("button", name="Cancel")
        self.continue_button = page.get_by_role("button", name="Continue")
        self.error_message = page.get_by_test_id("error")

        # Step Two - Overview
        self.overview_items = page.get_by_test_id("inventory-item")
        self.subtotal = page.get_by_test_id("subtotal-label")
        self.tax = page.get_by_test_id("tax-label")
        self.total = page.get_by_test_id("total-label")
        self.finish_button = page.get_by_role("button", name="Finish")

        # Complete
        self.complete_header = page.get_by_test_id("complete-header")
        self.back_home_button = page.get_by_role("button", name="Back Home")

    def opened(self) -> "CheckoutPage":
        """Ends on step one with the form ready for input."""
        expect(self.first_name_input).to_be_visible()
        return self

    def type_customer_info(self, first_name: str = "", last_name: str = "",
                           postal_code: str = "") -> None:
        """Types into the form without waiting: a defect check judges the fields."""
        self.first_name_input.fill(first_name)
        self.last_name_input.fill(last_name)
        self.postal_code_input.fill(postal_code)

    def fill_customer_info(self, first_name: str, last_name: str,
                           postal_code: str) -> None:
        """Fills the form and ends on each field holding what was typed into it."""
        self.type_customer_info(first_name, last_name, postal_code)
        self._holds(self.first_name_input, first_name, "First Name")
        self._holds(self.last_name_input, last_name, "Last Name")
        self._holds(self.postal_code_input, postal_code, "Postal Code")

    def typed_values(self) -> dict:
        """What the three fields hold right now, as the customer would read them."""
        return {"First Name": self.first_name_input.input_value(),
                "Last Name": self.last_name_input.input_value(),
                "Postal Code": self.postal_code_input.input_value()}

    def continue_to_overview(self) -> None:
        """Submits the customer details and ends on the order overview."""
        self.continue_button.click()
        self.arrived_at(STEP_TWO)
        expect(self.total).to_be_visible()

    def continue_refused(self) -> str:
        """Submits expecting a refusal, and returns what the store said."""
        self.continue_button.click()
        try:
            expect(self.error_message).to_be_visible()
        except AssertionError:
            raise AssertionError(f"checkout accepted the order and opened "
                                 f"{self.where()}") from None
        return self.error_message.inner_text().strip()

    def get_overview_items(self) -> list[dict]:
        """The lines the order overview lists, as the customer sees them."""
        items = []
        for item in self.overview_items.all():
            items.append({
                "name": item.get_by_test_id("inventory-item-name").inner_text().strip(),
                "price": item.get_by_test_id(
                    "inventory-item-price").inner_text().strip(),
                "quantity": item.get_by_test_id("item-quantity").inner_text().strip(),
            })
        return items

    def order_totals(self) -> dict:
        """The three money lines on the overview, as the customer reads them."""
        return {"item total": self.subtotal.inner_text().strip(),
                "tax": self.tax.inner_text().strip(),
                "total": self.total.inner_text().strip()}

    def click_finish(self) -> None:
        """Clicks Finish without waiting: a defect check judges the result."""
        self.finish_button.click()

    def finish_order(self) -> None:
        """Places the order and ends on its confirmation."""
        self.click_finish()
        try:
            expect(self.complete_header).to_have_text(THANK_YOU)
        except AssertionError:
            raise AssertionError(f"no confirmation appeared: the customer is still "
                                 f"on {self.where()}") from None

    def cancel(self) -> None:
        """Leaves checkout and ends back in the cart."""
        self.cancel_button.click()
        self.arrived_at(CART)

    def _holds(self, field, typed: str, name: str) -> None:
        try:
            expect(field).to_have_value(typed)
        except AssertionError:
            raise AssertionError(
                f"the {name} field holds {field.input_value()!r} after {typed!r} "
                f"was typed into it") from None
