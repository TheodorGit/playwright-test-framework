"""Base Page Object — shared logic for all page objects."""

from playwright.sync_api import Page


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page):
        self.page = page
