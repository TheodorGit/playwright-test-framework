# DEF-07: Finish does nothing, so no order can be placed

| Field | Entry |
|---|---|
| **Title** | SauceDemo, error_user build - the Finish button on the order overview never completes the order |
| **Source URL** | <https://www.saucedemo.com/checkout-step-two.html> |
| **Version in which the defect was initially detected** | SauceDemo publishes no build number. The defect belongs to the build served to `error_user`; this suite first recorded it on 2026-10-17, run `1017_1337f860`. |
| **Source / Owner** | QA. Found by the regression suite, pointed at the `error_user` build. |
| **Browsers / Devices** | Chromium 143 and Firefox 144, desktop at 1920x1080. |
| **User role** | Customer, signed in as `error_user`. |
| **Affected versions** | Every build served to `error_user` since this suite began checking. Not reproducible on the standard build of the same deploy. |
| **Severity** | Blocker. No order can be placed on this build at all. |
| **Status** | Open. Pinned by an automated check on every run. |

## Full defect description

On the order overview, clicking **Finish** does nothing. The page stays on the
overview, no confirmation appears, and no error is shown. The customer has
filled the form, reviewed the order and cannot pay.

## Preconditions

An account served the `error_user` build, one item in the cart, and checkout
step one completed so the order overview is on screen.

## Steps to reproduce and related screenshots

1. Open <https://www.saucedemo.com/> and sign in as `error_user`.
2. Add any product to the cart, open the cart and click **Checkout**.
3. Fill the form and click **Continue** to reach the order overview.
4. Click **Finish**.

![The order overview still on screen after Finish, with no confirmation](evidence/DEF-07-finish-does-not-complete-order.png)

## Actual results

The browser stays on `checkout-step-two.html`. No confirmation page, no
"Thank you for your order!" heading, and no error message anywhere.

## Expected results

The order completes and the confirmation page appears with the heading
"Thank you for your order!", as the standard build does.

## Movie / console logs / network requests

The run records the page it is still on after the click, and keeps a video and
a Playwright trace of the attempt.

## Defect verification on other builds and estimations

In the same run, the same order completes on the standard build and reaches the
confirmation page. The defect belongs to the build served to `error_user`.

## Scope and impact

Every customer served this build. The whole purchase funnel ends one click
short of the sale, with no fallback and nothing to tell the customer or support
what went wrong.

## Advanced info

Pinned by `tests/defects/test_known_defects.py::test_an_order_can_be_completed`,
check "the order reaches its confirmation". Reaching step two on this build
needs the Last Name field to be left empty, because the field takes no input
([DEF-08](DEF-08-last-name-accepts-no-input.md)) and checkout lets the empty
value through ([DEF-09](DEF-09-empty-last-name-accepted.md)).

## Notes

This build therefore carries three defects in one funnel: the field that takes
no input, the validation that lets it pass, and the Finish button that does
nothing. Only the last one blocks the order outright.
