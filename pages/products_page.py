"""Products Page Object for SauceDemo application."""

from playwright.sync_api import Page


class ProductsPage:
    """Page object for the products/inventory page."""

    # Locators
    TITLE = "[data-test='title']"
    INVENTORY_LIST = "[data-test='inventory-list']"
    INVENTORY_ITEM = "[data-test='inventory-item']"
    SORT_DROPDOWN = "[data-test='product-sort-container']"
    CART_BADGE = "[data-test='shopping-cart-badge']"
    CART_LINK = "[data-test='shopping-cart-link']"

    # Item-specific locators (use with nth())
    ITEM_NAME = "[data-test='inventory-item-name']"
    ITEM_PRICE = "[data-test='inventory-item-price']"
    ADD_TO_CART_BUTTON = "button[data-test^='add-to-cart']"
    REMOVE_BUTTON = "button[data-test^='remove']"

    def __init__(self, page: Page):
        self.page = page

    def get_page_title(self) -> str:
        """Get the page title."""
        return self.page.locator(self.TITLE).text_content()

    def get_product_count(self) -> int:
        """Get the number of products displayed."""
        return self.page.locator(self.INVENTORY_ITEM).count()

    def get_product_names(self) -> list[str]:
        """Get all product names on the page."""
        items = self.page.locator(self.ITEM_NAME).all()
        return [item.text_content() for item in items]

    def get_product_prices(self) -> list[str]:
        """Get all product prices on the page."""
        prices = self.page.locator(self.ITEM_PRICE).all()
        return [price.text_content() for price in prices]

    def add_product_to_cart(self, index: int = 0) -> None:
        """
        Add a product to cart by index.

        Args:
            index: The index of the product to add (0-based)
        """
        buttons = self.page.locator(self.ADD_TO_CART_BUTTON).all()
        if index < len(buttons):
            buttons[index].click()

    def add_product_by_name(self, product_name: str) -> None:
        """
        Add a product to cart by its name.

        Args:
            product_name: The exact name of the product to add
        """
        # Find the item container with matching name
        item = self.page.locator(self.INVENTORY_ITEM).filter(
            has=self.page.locator(self.ITEM_NAME, has_text=product_name)
        )
        item.locator(self.ADD_TO_CART_BUTTON).click()

    def remove_product_by_name(self, product_name: str) -> None:
        """Remove a product from cart by its name."""
        item = self.page.locator(self.INVENTORY_ITEM).filter(
            has=self.page.locator(self.ITEM_NAME, has_text=product_name)
        )
        item.locator(self.REMOVE_BUTTON).click()

    def get_cart_count(self) -> int:
        """Get the number of items in the cart badge."""
        badge = self.page.locator(self.CART_BADGE)
        if badge.is_visible():
            return int(badge.text_content())
        return 0

    def go_to_cart(self) -> None:
        """Navigate to the shopping cart."""
        self.page.click(self.CART_LINK)
        self.page.wait_for_load_state("networkidle")

    def sort_products(self, option: str) -> None:
        """
        Sort products by the given option.

        Args:
            option: Sort option value (az, za, lohi, hilo)
        """
        self.page.select_option(self.SORT_DROPDOWN, option)
