# Defect log

SauceDemo serves deliberately broken builds of the store to the `problem_user`
and `error_user` accounts. This log is the index of the defects my suite finds
in those builds, each written up the way I hand defects to a development team:
the environment, the exact steps, what happened against what should have
happened, the evidence, and whether it reproduces anywhere else.

Full reports live in [`docs/defects/`](docs/defects), one file per defect.

| ID | Defect | Build | Severity | Pinned by |
|---|---|---|---|---|
| [DEF-01](docs/defects/DEF-01-product-images-identical.md) | Every product shows the same broken image | `problem_user` | Major | `test_each_product_shows_its_own_image` |
| [DEF-02](docs/defects/DEF-02-price-sort-ignored.md) | Sorting by price silently does nothing | `problem_user` | Major | `test_price_sort_reorders_the_grid` |
| [DEF-03](docs/defects/DEF-03-last-name-writes-first-name.md) | The Last Name input writes into the First Name field | `problem_user` | Critical | `test_checkout_keeps_first_and_last_name_apart` |
| [DEF-04](docs/defects/DEF-04-add-to-cart-unresponsive.md) | Add to cart is unresponsive for some products | `problem_user` | Critical | `test_every_product_can_be_added_to_the_cart` |
| [DEF-05](docs/defects/DEF-05-grid-remove-unresponsive.md) | Remove on the product grid leaves the cart unchanged | `problem_user` | Major | `test_remove_on_the_grid_updates_the_cart` |
| [DEF-06](docs/defects/DEF-06-sort-error-dialog.md) | Sorting raises an error dialog and does not sort | `error_user` | Major | `test_sorting_completes_without_an_error_dialog` |
| [DEF-07](docs/defects/DEF-07-finish-does-not-complete-order.md) | Finish does nothing, so no order can be placed | `error_user` | Blocker | `test_an_order_can_be_completed` |
| [DEF-08](docs/defects/DEF-08-last-name-accepts-no-input.md) | The Last Name field accepts no input | `error_user` | Critical | `test_the_last_name_field_accepts_input` |
| [DEF-09](docs/defects/DEF-09-empty-last-name-accepted.md) | Checkout continues with an empty Last Name | `error_user` | Major | `test_checkout_refuses_an_empty_last_name` |

Reproduce all nine with `pytest -m defect`.

## How each report is written

Every report carries the same fields, so a developer gets the environment, the
steps, the evidence and the cross-build check in one place:

| Field | What it answers |
|---|---|
| Title | The site and build, then the issue in one line |
| Source URL | The exact page the defect appears on |
| Version in which the defect was initially detected | The build it was first seen on, and the run that recorded it |
| Source / Owner | QA, or the customer report it came from |
| Browsers / Devices | Where it was verified |
| User role | The account and role used to reproduce |
| Affected versions, severity, status | Scope in time, how much it hurts, where it stands |
| Full defect description | The issue in a couple of plain sentences |
| Preconditions | The data and settings that must exist before step 1 |
| Steps to reproduce and related screenshots | Numbered steps, with the evidence |
| Actual results | What happens, with the observed values |
| Expected results | What should happen, and on what grounds |
| Movie / console logs / network requests | Recordings, dialogs, logs, traces |
| Defect verification on other builds and estimations | Where it does and does not reproduce |
| Scope and impact | Which customers, orders and data are affected |
| Advanced info | The check that pins it, and what narrows it down |
| Notes | Related defects, open questions, follow-ups |

## How the defects are pinned

Each check is written as the **correct** behaviour and run against the broken
build. A defect that still reproduces is reported as a **known issue**: amber
in the report, with its evidence and a link to its report, and the run stays
green. A check that starts passing fails its test instead, which is the signal
that the defect is fixed and the check belongs in the regression suite.

Every run leaves the evidence behind: a screenshot taken at the failing check,
a video of the browser, a Playwright trace, and for DEF-06 the text of the
dialog the store raised, which no screenshot can show.

Each defect also gets a **positive control** in the same run: the same check on
the standard build. That is what pins a defect to a build rather than to the
storefront, and it is the evidence behind the "verification on other builds"
field in every report.
