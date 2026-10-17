"""The catalogue: what it lists, how it sorts, and what it puts in the cart."""

import re

from playwright.sync_api import Locator, Page, expect

from .base_page import BasePage
from .cart_page import CartPage

ADD = "Add to cart"
REMOVE = "Remove"
# The one button on a product card whose label flips as the cart changes.
CART_BUTTON = re.compile(rf"^({ADD}|{REMOVE})$")
CART = "cart.html"


class ProductsPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.title = page.get_by_test_id("title")
        self.inventory_items = page.get_by_test_id("inventory-item")
        self.item_names = page.get_by_test_id("inventory-item-name")
        self.item_prices = page.get_by_test_id("inventory-item-price")
        self.item_images = self.inventory_items.get_by_role("img")
        self.sort_dropdown = page.get_by_test_id("product-sort-container")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")
        self.cart_link = page.get_by_test_id("shopping-cart-link")

    def opened(self) -> "ProductsPage":
        """Ends on a painted catalogue, so every read that follows is safe."""
        expect(self.title).to_have_text("Products")
        expect(self.item_names).not_to_have_count(0)
        return self

    def get_product_names(self) -> list[str]:
        return [name.strip() for name in self.item_names.all_text_contents()]

    def get_product_prices(self) -> list[str]:
        return [price.strip() for price in self.item_prices.all_text_contents()]

    def get_product_image_sources(self) -> list[str | None]:
        return [image.get_attribute("src") for image in self.item_images.all()]

    def cart_count(self) -> int:
        """How many items the cart badge claims, zero when it is absent."""
        if self.cart_badge.count() == 0:
            return 0
        return int((self.cart_badge.inner_text() or "0").strip())

    def price_of(self, product_name: str) -> str:
        """The listed price of one product."""
        return self._item(product_name).get_by_test_id(
            "inventory-item-price").inner_text().strip()

    def cart_button_label(self, product_name: str) -> str:
        """What the product's cart button offers right now: Add or Remove."""
        return (self._cart_button(product_name).inner_text() or "").strip()

    def add_product_by_name(self, product_name: str) -> None:
        """Adds a product and ends on the button offering to remove it again."""
        self.click_add(product_name)
        self._button_reads(product_name, REMOVE)

    def remove_product_by_name(self, product_name: str) -> None:
        """Removes a product and ends on the button offering to add it again."""
        self.click_remove(product_name)
        self._button_reads(product_name, ADD)

    def click_add(self, product_name: str) -> None:
        """Clicks Add to cart without waiting: a defect check judges the result."""
        self._item(product_name).get_by_role("button", name=ADD).click()

    def click_remove(self, product_name: str) -> None:
        """Clicks Remove without waiting: a defect check judges the result."""
        self._item(product_name).get_by_role("button", name=REMOVE).click()

    def go_to_cart(self) -> CartPage:
        """Opens the cart and ends on the cart page, ready to be read."""
        self.cart_link.click()
        self.arrived_at(CART)
        return CartPage(self.page).opened()

    def sort_products(self, option: str) -> None:
        """Sorts the grid and ends on the control carrying the chosen option.

        The grid order is the real result, but it is also what DEF-02 and DEF-06
        are about, so waiting for it here would swallow them. The control is the
        furthest this can wait and still let those checks speak: on the broken
        builds the store re-renders the dropdown back to its old value, so this
        assertion fails there too, which is why the defect suite uses the
        select_sort twin below instead.
        """
        self.select_sort(option)
        try:
            expect(self.sort_dropdown).to_have_value(option)
        except AssertionError:
            raise AssertionError(
                f"the sort control went back to {self.sort_option_shown()} instead of "
                f"keeping {option}") from None

    def select_sort(self, option: str) -> None:
        """Chooses a sort option without waiting: a defect check judges the result."""
        self.sort_dropdown.select_option(option)

    def sort_option_shown(self) -> str:
        """The sort option the dropdown displays, as the customer reads it."""
        shown = self.sort_dropdown.get_by_role("option", selected=True).inner_text()
        return (shown or "").strip()

    def _item(self, product_name: str) -> Locator:
        return self.inventory_items.filter(
            has=self.item_names.filter(has_text=product_name))

    def _cart_button(self, product_name: str) -> Locator:
        return self._item(product_name).get_by_role("button", name=CART_BUTTON)

    def _button_reads(self, product_name: str, label: str) -> None:
        try:
            expect(self._cart_button(product_name)).to_have_text(label)
        except AssertionError:
            raise AssertionError(
                f"the cart button for {product_name} still reads "
                f"{self.cart_button_label(product_name)} after the click") from None
