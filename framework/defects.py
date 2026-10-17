"""
The defect catalogue: the open defects this suite pins.

Every entry has a written report under ``docs/defects/``. Tests name the
id, the report links to the document, and the document names the check,
so a red run and its write-up always point at each other.
"""

import os
from dataclasses import dataclass

DOCS_BASE_ENV = "QA_DEFECT_DOCS_BASE"
DEFAULT_DOCS_BASE = ("https://github.com/TheodorGit/playwright-test-framework"
                     "/blob/main/docs/defects")


@dataclass(frozen=True)
class Defect:
    id: str
    title: str
    build: str
    doc: str


CATALOGUE: dict[str, Defect] = {
    d.id: d for d in [
        Defect("DEF-01", "Every product shows the same broken image",
               "problem_user", "DEF-01-product-images-identical.md"),
        Defect("DEF-02", "Sorting by price silently does nothing",
               "problem_user", "DEF-02-price-sort-ignored.md"),
        Defect("DEF-03", "Last Name input writes into the First Name field",
               "problem_user", "DEF-03-last-name-writes-first-name.md"),
        Defect("DEF-04", "Add to cart is unresponsive for some products",
               "problem_user", "DEF-04-add-to-cart-unresponsive.md"),
        Defect("DEF-05", "Remove on the product grid leaves the cart unchanged",
               "problem_user", "DEF-05-grid-remove-unresponsive.md"),
        Defect("DEF-06", "Sorting raises an error dialog and does not sort",
               "error_user", "DEF-06-sort-error-dialog.md"),
        Defect("DEF-07", "Finish does nothing, so no order can be placed",
               "error_user", "DEF-07-finish-does-not-complete-order.md"),
        Defect("DEF-08", "The Last Name field accepts no input",
               "error_user", "DEF-08-last-name-accepts-no-input.md"),
        Defect("DEF-09", "Checkout continues with an empty Last Name",
               "error_user", "DEF-09-empty-last-name-accepted.md"),
    ]
}


def get(defect_id: str) -> Defect:
    try:
        return CATALOGUE[defect_id]
    except KeyError:
        raise KeyError(f"{defect_id} has no entry in the defect catalogue: add it "
                       f"to framework/defects.py with its report") from None


def url(defect_id: str) -> str:
    base = os.getenv(DOCS_BASE_ENV, DEFAULT_DOCS_BASE).rstrip("/")
    return f"{base}/{get(defect_id).doc}"


def pinned() -> list[Defect]:
    return list(CATALOGUE.values())
