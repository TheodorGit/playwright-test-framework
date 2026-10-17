# DEF-02: sorting by price silently does nothing

| Field | Entry |
|---|---|
| **Title** | SauceDemo, problem_user build - sorting the catalogue leaves the order untouched, with no error |
| **Source URL** | <https://www.saucedemo.com/inventory.html> |
| **Version in which the defect was initially detected** | SauceDemo publishes no build number. The defect belongs to the build served to `problem_user`; this suite first recorded it on 2026-10-17, run `1017_1337f860`. |
| **Source / Owner** | QA. Found by the regression suite, pointed at the `problem_user` build. |
| **Browsers / Devices** | Chromium 143 and Firefox 144, desktop at 1920x1080. |
| **User role** | Customer, signed in as `problem_user`. |
| **Affected versions** | Every build served to `problem_user` since this suite began checking. Not reproducible on the standard build of the same deploy. |
| **Severity** | Major. A core browsing feature fails, and fails quietly. |
| **Status** | Open. Pinned by an automated check on every run. |

## Full defect description

Choosing an option in the catalogue sort dropdown leaves the grid in its
original order. The dropdown shows the chosen option, so the page claims the
sort was applied, and nothing tells the customer otherwise.

## Preconditions

An account served the `problem_user` build, and a catalogue of several products
at different prices.

## Steps to reproduce and related screenshots

1. Open <https://www.saucedemo.com/> and sign in as `problem_user`.
2. Choose **Price (low to high)** in the sort dropdown.
3. Read the prices from left to right.

![The grid after choosing Price (low to high), still in its original order](evidence/DEF-02-price-sort-ignored.png)

## Actual results

The grid keeps its original order after the sort is chosen:
`$29.99, $9.99, $15.99, $49.99, $7.99, $15.99`. The dropdown shows the selected
option, and no error appears anywhere on the page.

## Expected results

The grid reorders to `$7.99, $9.99, $15.99, $15.99, $29.99, $49.99`, and the
same for the other three sort options.

## Movie / console logs / network requests

No console error and no request accompany the choice: the page simply does not
reorder. The check records the order it read, which is the sequence above.

## Defect verification on other builds and estimations

In the same run, the same sort works on the standard build, which comes back
with `$7.99` first and `$49.99` last. The defect belongs to the build served to
`problem_user`.

## Scope and impact

Every customer served this build. Sorting is the only way to compare prices
across the catalogue, so a shopper looking for the cheapest item is shown the
wrong order with no signal that anything failed.

## Advanced info

Pinned by `tests/defects/test_known_defects.py::test_price_sort_reorders_the_grid`,
check "sorting by price reorders the grid". The regression suite's own four
sort tests fail against this build, which is how the defect was first seen.

## Notes

The `error_user` build fails the same feature loudly rather than quietly, which
is [DEF-06](DEF-06-sort-error-dialog.md). Worth fixing together: one build
hides the failure, the other announces it.
