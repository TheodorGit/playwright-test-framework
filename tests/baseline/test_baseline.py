"""
What the storefront looked like before this run acted on it.

The baseline is read first and reported first, so a later check that
disagrees with it has something honest to disagree with.
"""

from pages import ProductsPage
from tests import shop

CATALOGUE_SIZE = 6


def _names(products: ProductsPage) -> list[str]:
    names = products.get_product_names()
    assert len(names) == CATALOGUE_SIZE, (
        f"expected {CATALOGUE_SIZE} products, the catalogue listed "
        f"{len(names)}: {names}")
    nameless = [n for n in names if not (n or "").strip()]
    assert not nameless, f"a product is listed without a name: {names}"
    return names


def _prices(products: ProductsPage) -> list:
    prices = [shop.amount(text) for text in products.get_product_prices()]
    assert len(prices) == CATALOGUE_SIZE, (
        f"expected {CATALOGUE_SIZE} prices, read {len(prices)}: {prices}")
    free = [p for p in prices if p <= 0]
    assert not free, f"a product is priced at zero or less: {prices}"
    return prices


def _images(products: ProductsPage) -> list[str]:
    sources = products.get_product_image_sources()
    missing = [s for s in sources if not s]
    assert not missing, f"a product has no image: {sources}"
    distinct = sorted(set(sources))
    assert len(distinct) == len(sources), (
        f"{len(sources)} products show only {len(distinct)} distinct image(s): "
        f"{', '.join(str(source) for source in distinct)}")
    return sources


def test_storefront_baseline(authenticated_page, checks):
    """Reads the catalogue the rest of the run works from."""
    products = ProductsPage(authenticated_page)

    names = checks.check(
        "the catalogue lists every product",
        lambda: _names(products),
        expected=f"{CATALOGUE_SIZE} products, each with a name",
        found=lambda read: f"{len(read)} products listed",
        ui=True)
    checks.check(
        "every product carries a price",
        lambda: _prices(products),
        expected="a price above zero on every product",
        found=lambda read: (f"{len(read)} prices, {shop.money(min(read))} to "
                            f"{shop.money(max(read))}"))
    checks.check(
        "every product shows its own image",
        lambda: _images(products),
        expected="one distinct image per product",
        found=lambda read: f"{len(set(read))} distinct images")
    checks.check(
        "the cart starts empty",
        lambda: _assert_empty(products),
        expected="no cart badge before this run adds anything",
        ui=True)
    checks.add_metadata("catalogue", names)
    checks.tally("products read", len(names))


def _assert_empty(products: ProductsPage):
    count = products.cart_count()
    assert count == 0, f"the cart already holds {count} item(s) before the run acted"
