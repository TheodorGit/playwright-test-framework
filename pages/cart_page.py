"""Cart Page Object for SauceDemo application."""

from playwright.sync_api import Page


class CartPage:
    """Page object for the shopping cart page."""

    # Locators
    TITLE = "[data-test='title']"
    CART_ITEM = "[data-test='inventory-item']"
    ITEM_NAME = "[data-test='inventory-item-name']"
    ITEM_PRICE = "[data-test='inventory-item-price']"
    ITEM_QUANTITY = "[data-test='item-quantity']"
    REMOVE_BUTTON = "button[data-test^='remove']"
    CONTINUE_SHOPPING = "[data-test='continue-shopping']"
    CHECKOUT_BUTTON = "[data-test='checkout']"

    def __init__(self, page: Page):
        self.page = page

    def get_page_title(self) -> str:
        """Get the page title."""
        return self.page.locator(self.TITLE).text_content()

    def get_cart_items(self) -> list[dict]:
        """
        Get all items in the cart with their details.

        Returns:
            List of dicts with 'name', 'price', 'quantity' keys
        """
        items = []
        cart_items = self.page.locator(self.CART_ITEM).all()

        for item in cart_items:
            items.append({
                "name": item.locator(self.ITEM_NAME).text_content(),
                "price": item.locator(self.ITEM_PRICE).text_content(),
                "quantity": item.locator(self.ITEM_QUANTITY).text_content()
            })

        return items

    def get_item_count(self) -> int:
        """Get the number of items in the cart."""
        return self.page.locator(self.CART_ITEM).count()

    def remove_item(self, product_name: str) -> None:
        """
        Remove an item from the cart by name.

        Args:
            product_name: The name of the product to remove
        """
        item = self.page.locator(self.CART_ITEM).filter(
            has=self.page.locator(self.ITEM_NAME, has_text=product_name)
        )
        item.locator(self.REMOVE_BUTTON).click()

    def continue_shopping(self) -> None:
        """Go back to the products page."""
        self.page.click(self.CONTINUE_SHOPPING)
        self.page.wait_for_load_state("networkidle")

    def proceed_to_checkout(self) -> None:
        """Proceed to the checkout page."""
        self.page.click(self.CHECKOUT_BUTTON)
        self.page.wait_for_load_state("networkidle")
