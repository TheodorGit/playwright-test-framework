# Working rules

`CLAUDE.md` imports this file, so it loads into every AI-assisted session. Keep it
short; fix a wrong line here rather than noting it elsewhere.

## Boundaries
- `framework/` is product-agnostic: it never imports `pages/` or `tests/` and names no
  storefront feature. Product meaning reaches it through one seam, the defect
  catalogue in `framework/defects.py`.
- `pages/` knows where things are on screen. `tests/` knows what is worth proving. A
  test never reaches for a raw locator.
- Targets are public demo sites by design (SauceDemo, restful-booker). Nothing here
  points at a client environment or carries client data.

## Testing standards
- A test proves an outcome on a surface other than the one it drove: the cart read
  back against the catalogue, the order total recomputed from the prices the run read,
  the API list against its detail view. Where the storefront offers no second surface,
  say so in the test and prove what there is. `test_checkout_keeps_what_was_typed` is
  the standing case: SauceDemo never shows the customer's name again.
- Every UI action ends on its visible result before the next action. The action lives
  in `pages/`, and so does the `expect()` that confirms it landed.
- An action that deliberately does not wait is named for the gesture rather than the
  outcome (`click_add`, `select_sort`, `type_customer_info`), and exists only so a
  defect check can judge a result that never arrives.
- A failure belongs at the action when the action's own contract broke and the test had
  declared nothing about it. It belongs inside a check when the test's declared
  expectation is about exactly what that action does, which means the action moves into
  the check that judges it. A failure reported under an expectation it does not answer
  is a mislabelled failure, and worse than one reported at the action.
- Never sleep for what can be polled. `expect()` retries; `sleep()` does not appear.
- Locators: role, text, label, placeholder, test id. CSS only as a last resort, with a
  one-line reason. No XPath.
- Every check declares what it expected before it runs, in the words the report reader
  would use. Compare against what the run itself did, never against a tolerance.
- A report never implies a number the run did not measure. A narrowed run says what
  was selected and what deselected it, above any verdict. A count of checks says it is
  what the run recorded, because a test that stopped early never declared the rest, and
  no total is borrowed from another run or written into the code.
- Every documented defect carries a positive control in the same run: the same check on
  the standard build, which is what pins the defect to a build.

## Defect reports
- One file per defect under `docs/defects/`, in the field template `BUGS.md` describes,
  with `BUGS.md` as the index. Ids are `DEF-NN`; severity is Blocker, Critical,
  Major or Minor, and the entry says what the rating rests on, not just the word.
- A defect is pinned with `checks.known_defect(...)` naming its id. Still reproducing is
  a known issue and keeps the run green; fixed fails the test, which is the signal to
  promote the check into the regression suite.
- Every entry in `framework/defects.py` has a report. `framework/tests` fails if one
  does not.

## Style
- Plain ASCII in code. No em dashes anywhere, including commit messages.
- A file may open with one line saying what it is. A docstring earns its place by
  telling a reader something the code cannot; it never restates the signature.
- Comment only a reason the code cannot show, in one line.
- Commit messages: one subject line, and no AI attribution.

## Running it
- `pytest -n auto` for the suite, `pytest framework/tests` for the framework's own
  tests, `pytest tests/<stage>` for one stage.
- Two markers only, `api` and `defect`, because each selects a set no directory can
  express and each is a CI job. Anything a path already says is not a marker.
- `pip install pre-commit && pre-commit install` sets up the ruff hook. Lint with
  `ruff check .`; the config lives in `pyproject.toml`.
