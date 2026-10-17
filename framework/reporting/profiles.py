"""
How this suite presents itself in the report.

One plan is the single source of truth for a test's section, its readable
title and the order it appears in, so the report reads like a run of the
shop rather than a list of function names.
"""

SUITE_TITLE = "SauceDemo storefront regression"
PASSED_SUBHEAD = "Every check below ran against the live storefront."

PLAN: list[tuple[str, list[tuple[str, str]]]] = [
    ("BASELINE", [
        ("test_storefront_baseline",
         "Baseline readings before the run acts"),
    ]),
    ("ACCESS", [
        ("test_sign_in_with_valid_credentials",
         "Sign in with valid credentials"),
        ("test_wrong_password_is_refused",
         "A wrong password is refused, and says so"),
        ("test_unknown_username_is_refused",
         "An unknown username is refused"),
        ("test_locked_out_account_is_refused",
         "A locked-out account is refused, and told why"),
        ("test_empty_credentials_are_refused",
         "Empty credentials are refused field by field"),
    ]),
    ("BROWSE", [
        ("test_catalogue_lists_every_product",
         "The catalogue lists every product, with a price and an image"),
        ("test_add_to_cart_from_the_grid",
         "Add to cart from the grid, badge and button included"),
        ("test_remove_from_cart_on_the_grid",
         "Remove on the grid empties the cart again"),
        ("test_sort_by_price_low_to_high",
         "Sort by price, low to high"),
        ("test_sort_by_price_high_to_low",
         "Sort by price, high to low"),
        ("test_sort_by_name_a_to_z",
         "Sort by name, A to Z"),
        ("test_sort_by_name_z_to_a",
         "Sort by name, Z to A"),
    ]),
    ("CART", [
        ("test_cart_starts_empty",
         "The cart starts empty"),
        ("test_cart_holds_exactly_what_was_added",
         "The cart holds exactly what the run added"),
        ("test_cart_line_shows_name_price_and_quantity",
         "A cart line shows the name, price and quantity"),
        ("test_removing_a_line_leaves_the_rest",
         "Removing one line leaves the rest untouched"),
        ("test_continue_shopping_returns_to_the_catalogue",
         "Continue shopping returns to the catalogue"),
    ]),
    ("CHECKOUT", [
        ("test_checkout_requires_a_first_name",
         "Checkout refuses a missing first name"),
        ("test_checkout_requires_a_last_name",
         "Checkout refuses a missing last name"),
        ("test_checkout_requires_a_postal_code",
         "Checkout refuses a missing postal code"),
        ("test_checkout_keeps_what_was_typed",
         "The form keeps exactly what the customer typed"),
        ("test_cancel_returns_to_the_cart",
         "Cancelling checkout returns to the cart"),
    ]),
    ("PURCHASE", [
        ("test_single_item_purchase",
         "Buy one item, from sign-in to confirmation"),
        ("test_multi_item_purchase",
         "Buy three items in one order"),
        ("test_purchase_after_removing_a_line",
         "Remove a line, then buy what is left"),
    ]),
    ("BOOKING API", [
        ("test_created_booking_matches_the_contract",
         "A created booking honours the documented contract"),
        ("test_read_booking_matches_the_contract",
         "A booking read back honours the documented contract"),
        ("test_auth_refuses_wrong_credentials",
         "Auth issues no token for wrong credentials"),
        ("test_missing_booking_returns_404",
         "A booking that does not exist answers 404"),
        ("test_booking_lifecycle",
         "A booking created, updated, read back and deleted"),
    ]),
    ("VERIFICATION", [
        ("test_order_total_matches_the_run",
         "The order total is exactly what the run put in the cart"),
        ("test_cart_agrees_with_the_catalogue",
         "Cart lines agree with the catalogue the run read"),
        ("test_api_list_and_detail_agree",
         "The API list and the detail view agree on the run's booking"),
    ]),
    ("KNOWN DEFECTS", [
        ("test_each_product_shows_its_own_image",
         "Every product shows its own image"),
        ("test_price_sort_reorders_the_grid",
         "Sorting by price reorders the grid"),
        ("test_checkout_keeps_first_and_last_name_apart",
         "Checkout keeps the first and last name apart"),
        ("test_every_product_can_be_added_to_the_cart",
         "Every product can be added to the cart"),
        ("test_remove_on_the_grid_updates_the_cart",
         "Remove on the grid updates the cart"),
        ("test_sorting_completes_without_an_error_dialog",
         "Sorting completes without an error dialog"),
        ("test_an_order_can_be_completed",
         "An order can be completed"),
        ("test_the_last_name_field_accepts_input",
         "The Last Name field accepts what is typed into it"),
        ("test_checkout_refuses_an_empty_last_name",
         "Checkout refuses an empty last name"),
    ]),
]

FACT_ORDER = ["products read", "items added", "orders placed",
              "bookings created", "defects pinned"]

_SECTION_OF = {func: section for section, funcs in PLAN for func, _ in funcs}
_TITLE_OF = {func: title for _, funcs in PLAN for func, title in funcs}
_ORDER = [func for _, funcs in PLAN for func, _ in funcs]


def section_for(func: str) -> str:
    return _SECTION_OF.get(func, "OTHER")


def title_for(func: str) -> str:
    return _TITLE_OF.get(func, func)


def number_for(func: str) -> int:
    """The test's place in the run, or 0 for a test the plan does not name."""
    return _ORDER.index(func) + 1 if func in _ORDER else 0


def sections_in_order() -> list[str]:
    return [section for section, _ in PLAN] + ["OTHER"]


def facts(tally: dict) -> list[tuple[str, int]]:
    """What the run actually did, in a fixed order, skipping what it did not."""
    known = [(key, tally[key]) for key in FACT_ORDER if tally.get(key)]
    extra = [(k, v) for k, v in sorted(tally.items()) if k not in FACT_ORDER and v]
    return known + extra
