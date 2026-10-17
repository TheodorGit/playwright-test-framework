"""Signing in: who gets in, who is refused, and what they are told."""

from pages import LoginPage, ProductsPage

LOCKED_USER = "locked_out_user"
UNKNOWN_USER = "invalid_user"
NO_MATCH = "Username and password do not match any user in this service"
LOCKED_OUT = "Sorry, this user has been locked out"
USERNAME_REQUIRED = "Username is required"
PASSWORD_REQUIRED = "Password is required"
NO_SESSION = "You can only access"


def _says(shown: str, wanted: str) -> str:
    assert wanted in shown, f"the store said: {shown}"
    return shown


def _no_session(login: LoginPage) -> str:
    """Proves the refusal left no session, from the catalogue's own side."""
    return _says(login.catalogue_refuses_direct_entry(), NO_SESSION)


def test_sign_in_with_valid_credentials(page, checks, test_credentials):
    login = LoginPage(page)
    login.navigate()

    checks.check("the storefront opens on the catalogue",
                 lambda: login.sign_in(test_credentials["username"],
                                       test_credentials["password"]),
                 expected="the inventory page, not the login form", ui=True)
    checks.check("the catalogue belongs to a signed-in customer",
                 lambda: ProductsPage(page).opened().get_product_names(),
                 expected="the Products page, listing the catalogue",
                 found=lambda names: f"{len(names)} products listed")


def test_wrong_password_is_refused(page, checks, test_credentials):
    login = LoginPage(page)
    login.navigate()

    checks.check("the attempt is refused, and says why",
                 lambda: _says(login.sign_in_refused(
                     test_credentials["username"], "wrong_password"), NO_MATCH),
                 expected=f"the message: {NO_MATCH}", ui=True)
    checks.check("the refusal left no session behind",
                 lambda: _no_session(login),
                 expected="opening the catalogue directly is refused too", ui=True)


def test_unknown_username_is_refused(page, checks):
    login = LoginPage(page)
    login.navigate()

    shown = checks.check("the attempt is refused, and says why",
                         lambda: _says(login.sign_in_refused(
                             UNKNOWN_USER, "any_password"), NO_MATCH),
                         expected=f"the message: {NO_MATCH}", ui=True)
    checks.check("the message does not say which half was wrong",
                 lambda: _names_no_field(shown),
                 expected="one message for both, so it names no account")


def test_locked_out_account_is_refused(page, checks):
    login = LoginPage(page)
    login.navigate()

    checks.check("the locked account is refused, and told why",
                 lambda: _says(login.sign_in_refused(LOCKED_USER, "secret_sauce"),
                               LOCKED_OUT),
                 expected=f"the message: {LOCKED_OUT}", ui=True)
    checks.check("the refusal left no session behind",
                 lambda: _no_session(login),
                 expected="opening the catalogue directly is refused too", ui=True)


def test_empty_credentials_are_refused(page, checks):
    login = LoginPage(page)
    login.navigate()

    checks.check("an empty form names the field it needs first",
                 lambda: _says(login.sign_in_refused("", ""), USERNAME_REQUIRED),
                 expected=f"the message: {USERNAME_REQUIRED}", ui=True)
    checks.check("a username without a password names the password",
                 lambda: _says(login.sign_in_refused("standard_user", ""),
                               PASSWORD_REQUIRED),
                 expected=f"the message: {PASSWORD_REQUIRED}", ui=True)


def _names_no_field(shown: str) -> str:
    leaked = [field for field in ("Username is", "Password is") if field in shown]
    assert not leaked, f"the refusal names a field: {shown}"
    return shown
