"""Cart Page Object for SauceDemo application."""

from playwright.sync_api import Page

from .base_page import BasePage


class CartPage(BasePage):
    """Page object for the shopping cart page."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.get_by_test_id("title")
        self.cart_items = page.get_by_test_id("inventory-item")
        self.continue_shopping_button = page.get_by_test_id("continue-shopping")
        self.checkout_button = page.get_by_test_id("checkout")

    def get_page_title(self) -> str:
        """Get the page title."""
        return self.title.text_content()

    def get_cart_items(self) -> list[dict]:
        """Get all items in the cart with their details."""
        items = []
        for item in self.cart_items.all():
            items.append({
                "name": item.get_by_test_id("inventory-item-name").text_content(),
                "price": item.get_by_test_id("inventory-item-price").text_content(),
                "quantity": item.get_by_test_id("item-quantity").text_content(),
            })
        return items

    def get_item_count(self) -> int:
        """Get the number of items in the cart."""
        return self.cart_items.count()

    def remove_item(self, product_name: str) -> None:
        """Remove an item from the cart by name."""
        item = self.cart_items.filter(
            has=self.page.get_by_test_id("inventory-item-name").filter(
                has_text=product_name
            )
        )
        item.locator("button[data-test^='remove']").click()

    def continue_shopping(self) -> None:
        """Go back to the products page."""
        self.continue_shopping_button.click()

    def proceed_to_checkout(self) -> None:
        """Proceed to the checkout page."""
        self.checkout_button.click()
