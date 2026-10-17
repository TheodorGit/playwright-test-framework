"""The cart: what it holds, and the two ways out of it."""

from playwright.sync_api import Locator, Page, expect

from .base_page import BasePage
from .checkout_page import CheckoutPage

CATALOGUE = "inventory.html"
CHECKOUT_STEP_ONE = "checkout-step-one.html"
REMOVE = "Remove"


class CartPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.get_by_test_id("title")
        self.cart_items = page.get_by_test_id("inventory-item")
        self.continue_shopping_button = page.get_by_role(
            "button", name="Continue Shopping")
        self.checkout_button = page.get_by_role("button", name="Checkout")

    def opened(self) -> "CartPage":
        """Ends on a painted cart, so every read that follows is safe."""
        expect(self.title).to_have_text("Your Cart")
        return self

    def get_cart_items(self) -> list[dict]:
        """The lines the cart holds, as the customer reads them."""
        items = []
        for item in self.cart_items.all():
            items.append({
                "name": item.get_by_test_id("inventory-item-name").inner_text().strip(),
                "price": item.get_by_test_id(
                    "inventory-item-price").inner_text().strip(),
                "quantity": item.get_by_test_id("item-quantity").inner_text().strip(),
            })
        return items

    def remove_item(self, product_name: str) -> None:
        """Removes a line and ends on that line being gone."""
        line = self._line(product_name)
        line.get_by_role("button", name=REMOVE).click()
        try:
            expect(line).to_have_count(0)
        except AssertionError:
            raise AssertionError(f"the line for {product_name} is still in the cart "
                                 f"after Remove") from None

    def continue_shopping(self) -> None:
        """Goes back to the catalogue and ends there."""
        self.continue_shopping_button.click()
        self.arrived_at(CATALOGUE)

    def proceed_to_checkout(self) -> CheckoutPage:
        """Starts checkout and ends on step one, ready for the customer details."""
        self.checkout_button.click()
        self.arrived_at(CHECKOUT_STEP_ONE)
        return CheckoutPage(self.page).opened()

    def _line(self, product_name: str) -> Locator:
        return self.cart_items.filter(
            has=self.page.get_by_test_id("inventory-item-name").filter(
                has_text=product_name))
