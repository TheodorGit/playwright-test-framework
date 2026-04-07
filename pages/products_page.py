"""Products Page Object for SauceDemo application."""

from playwright.sync_api import Page

from .base_page import BasePage


class ProductsPage(BasePage):
    """Page object for the products/inventory page."""

    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.get_by_test_id("title")
        self.inventory_items = page.get_by_test_id("inventory-item")
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.item_prices = page.get_by_test_id("inventory-item-price")
        self.sort_dropdown = page.get_by_test_id("product-sort-container")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")
        self.cart_link = page.get_by_test_id("shopping-cart-link")

    def get_page_title(self) -> str:
        """Get the page title."""
        return self.title.text_content()

    def get_product_count(self) -> int:
        """Get the number of products displayed."""
        return self.inventory_items.count()

    def get_product_names(self) -> list[str]:
        """Get all product names on the page."""
        return [item.text_content() for item in self.item_names.all()]

    def get_product_prices(self) -> list[str]:
        """Get all product prices on the page."""
        return [price.text_content() for price in self.item_prices.all()]

    def add_product_to_cart(self, index: int = 0) -> None:
        """Add a product to cart by index."""
        self.inventory_items.nth(index).locator(
            "button[data-test^='add-to-cart']"
        ).click()

    def add_product_by_name(self, product_name: str) -> None:
        """Add a product to cart by its name."""
        item = self.inventory_items.filter(
            has=self.page.get_by_test_id("inventory-item-name").filter(
                has_text=product_name
            )
        )
        item.locator("button[data-test^='add-to-cart']").click()

    def remove_product_by_name(self, product_name: str) -> None:
        """Remove a product from cart by its name."""
        item = self.inventory_items.filter(
            has=self.page.get_by_test_id("inventory-item-name").filter(
                has_text=product_name
            )
        )
        item.locator("button[data-test^='remove']").click()

    def get_cart_count(self) -> int:
        """Get the number of items in the cart badge."""
        if self.cart_badge.is_visible():
            return int(self.cart_badge.text_content())
        return 0

    def go_to_cart(self) -> None:
        """Navigate to the shopping cart."""
        self.cart_link.click()

    def sort_products(self, option: str) -> None:
        """Sort products by the given option (az, za, lohi, hilo)."""
        self.sort_dropdown.select_option(option)
