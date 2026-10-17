"""The catalogue: what it lists, what it adds to the cart, how it sorts."""

import pytest

from pages import ProductsPage
from tests import shop

pytestmark = [pytest.mark.functional, pytest.mark.regression]

BACKPACK = "Sauce Labs Backpack"
CATALOGUE_SIZE = 6


def _complete_listing(products: ProductsPage) -> int:
    names = products.get_product_names()
    prices = products.get_product_prices()
    images = products.get_product_image_sources()
    assert len(names) == len(prices) == len(images) == CATALOGUE_SIZE, (
        f"{len(names)} names, {len(prices)} prices and {len(images)} images: a "
        f"product is listed without all three")
    return len(names)


def _own_images(products: ProductsPage) -> int:
    images = products.get_product_image_sources()
    distinct = set(images)
    assert len(distinct) == len(images), (
        f"{len(images)} products share {len(distinct)} images: {sorted(distinct)}")
    return len(distinct)


def _reorder(products: ProductsPage, option: str) -> dict:
    before = set(products.get_product_names())
    products.sort_products(option)
    return {"before": before,
            "names": products.get_product_names(),
            "prices": [shop.amount(text) for text in products.get_product_prices()]}


def _assert_same_products(read: dict):
    after = set(read["names"])
    assert after == read["before"], (
        f"sorting changed which products are listed: "
        f"missing {sorted(read['before'] - after)}, extra {sorted(after - read['before'])}")


def test_catalogue_lists_every_product(authenticated_page, steps):
    products = ProductsPage(authenticated_page)

    steps.step("the catalogue lists a name, a price and an image for each product",
               lambda: _complete_listing(products),
               expected=f"{CATALOGUE_SIZE} complete listings",
               found=lambda count: f"{count} complete listings",
               ui=True)
    steps.step("no two products share an image",
               lambda: _own_images(products),
               expected="one distinct image per product",
               found=lambda count: f"{count} distinct images")


def test_add_to_cart_from_the_grid(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    products.add_product_by_name(BACKPACK)

    steps.step("the cart badge counts the item",
               lambda: _assert_count(products, 1),
               expected="a badge reading 1", ui=True)
    steps.step("the product now offers to remove it",
               lambda: _assert_button(products, BACKPACK, "Remove"),
               expected="the button reads Remove, so the page agrees it is in")
    steps.tally("items added", 1)


def test_remove_from_cart_on_the_grid(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    products.add_product_by_name(BACKPACK)
    _assert_count(products, 1)
    products.remove_product_by_name(BACKPACK)

    steps.step("the badge is gone, not merely wrong",
               lambda: _assert_count(products, 0),
               expected="no badge at all once the cart is empty", ui=True)
    steps.step("the product offers to add it again",
               lambda: _assert_button(products, BACKPACK, "Add to cart"),
               expected="the button reads Add to cart")
    steps.tally("items added", 1)


def test_sort_by_price_low_to_high(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    read = _reorder(products, "lohi")

    steps.step("the grid is ordered by price, cheapest first",
               lambda: _assert_ordered(read["prices"], reverse=False),
               expected="every price at least the one before it",
               found=lambda _: f"{shop.money(read['prices'][0])} first, "
                               f"{shop.money(read['prices'][-1])} last",
               ui=True)
    steps.step("sorting kept the same products",
               lambda: _assert_same_products(read),
               expected=f"the same {CATALOGUE_SIZE} products, in a new order")


def test_sort_by_price_high_to_low(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    read = _reorder(products, "hilo")

    steps.step("the grid is ordered by price, dearest first",
               lambda: _assert_ordered(read["prices"], reverse=True),
               expected="every price at most the one before it",
               found=lambda _: f"{shop.money(read['prices'][0])} first, "
                               f"{shop.money(read['prices'][-1])} last",
               ui=True)
    steps.step("sorting kept the same products",
               lambda: _assert_same_products(read),
               expected=f"the same {CATALOGUE_SIZE} products, in a new order")


def test_sort_by_name_a_to_z(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    read = _reorder(products, "az")

    steps.step("the grid is ordered by name, A to Z",
               lambda: _assert_ordered(read["names"], reverse=False),
               expected="names in ascending order", ui=True)
    steps.step("sorting kept the same products",
               lambda: _assert_same_products(read),
               expected=f"the same {CATALOGUE_SIZE} products, in a new order")


def test_sort_by_name_z_to_a(authenticated_page, steps):
    products = ProductsPage(authenticated_page)
    read = _reorder(products, "za")

    steps.step("the grid is ordered by name, Z to A",
               lambda: _assert_ordered(read["names"], reverse=True),
               expected="names in descending order", ui=True)
    steps.step("sorting kept the same products",
               lambda: _assert_same_products(read),
               expected=f"the same {CATALOGUE_SIZE} products, in a new order")


def _assert_count(products: ProductsPage, expected: int):
    count = products.cart_count()
    assert count == expected, f"the cart badge says {count}, expected {expected}"


def _assert_button(products: ProductsPage, name: str, label: str):
    found = (products.cart_button_label(name) or "").strip()
    assert found == label, f"the button reads {found}, not {label}"


def _assert_ordered(values: list, reverse: bool):
    want = sorted(values, reverse=reverse)
    # Printed as plain text: a report is read by people, not by Python.
    read = ", ".join(str(value) for value in values)
    ordered = ", ".join(str(value) for value in want)
    assert values == want, f"the grid reads {read}, which in order is {ordered}"
