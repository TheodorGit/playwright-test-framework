"""What every page object shares: the page, its wait budget, and where it landed."""

import re

from playwright.sync_api import Page, expect

from config import settings


class BasePage:

    def __init__(self, page: Page):
        self.page = page
        # One budget for an action and for the expect() that closes it.
        page.set_default_timeout(settings.ui_timeout_ms)
        expect.set_options(timeout=settings.ui_timeout_ms)

    def arrived_at(self, page_name: str) -> None:
        """Ends a navigating action on the page it was meant to reach."""
        try:
            expect(self.page).to_have_url(re.compile(re.escape(page_name)))
        except AssertionError:
            raise AssertionError(f"the store stayed on {self.where()} instead of "
                                 f"opening {page_name}") from None

    def watch_dialogs(self) -> list[str]:
        """Dismisses every dialog the store raises from now on, recording the text.

        The returned list fills as they are raised. Playwright holds the action
        that raised one until the handler returns, so a dialog is already in the
        list by the time that action does.
        """
        raised: list[str] = []

        def remember(dialog):
            raised.append(dialog.message)
            dialog.dismiss()

        self.page.on("dialog", remember)
        return raised

    def where(self) -> str:
        """The page the browser is on, named the way a report should name it."""
        return self.page.url.rsplit("/", 1)[-1] or self.page.url
